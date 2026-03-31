from typing import Optional, Tuple, Dict, Set, List, Any
from datetime import date
from glob import glob

from src.models import Auto, FinancialPlan
from pydantic import ValidationError

from src.logger import setup_logging
from src.database import engine, create_db_n_tables
from sqlmodel import Session, select
from src import settings

import requests
import logging
import random
import json
import time
import sys
import os


# Configurando logger
setup_logging()
logger = logging.getLogger(__name__)


# Example: 'https://www.kavak.com/api/vip-ui/mx/calculator/468814?upfront-amount=116499'
FINANCIAL_API = 'https://www.kavak.com/api/vip-ui/mx/calculator'
DEFAULT_HEADERS = {
    'Accept-Language': 'es-MX,es;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
}
BATCH_SIZE = 60 # 6 Registros de planes por cada 10 autos


# Configuracion
def get_raw_json_path() -> Optional[str]:
    """Retorna el ultimo archivo json en el directorio de datos crudos"""
    JSON_FILES = glob(f"{settings.RAW_JSON_DIR}/*.jsonl")
    JSON_FILES.sort()
    
    try:
        json_path = JSON_FILES[-1]
        logger.info("Archivo encontrado: %s", json_path)
    except IndexError:
        logger.error("Archivo json no encontrado.")
        sys.exit()

    return json_path


def get_minimum_upfront_amount(price: int) -> int:
    """Retorna el 16% sobre el valor del vehiculo como enganche"""
    return int(price * 0.16)


def get_fresh_session() -> requests.Session:
    """Crea una sesion nueva, limpiando asi los headers y cookies"""
    s = requests.Session()
    s.headers.update(DEFAULT_HEADERS)
    ua = random.choice(settings.USER_AGENTS)
    s.headers.update({'User-Agent': ua})
    return s


def api_requester(auto_id: str, slug: str, price: int, session: requests.Session) -> Optional[requests.Response]:
    """Realiza las peticiones a la API Financiera de Kavak para obtener los distintos planes de financiamiento."""
    api_url = f"{FINANCIAL_API}/{auto_id}"
    upfront_amount = get_minimum_upfront_amount(price)
    query_params = {
        'upfront-amount': upfront_amount
    }

    dynamic_headers = {
        'Referer' : f"{slug}?id={auto_id}"
    }

    try:
        response = session.get(api_url, headers=dynamic_headers, params=query_params, timeout=10)
        response.raise_for_status()
        return response

    except requests.exceptions.RequestException as e:
        logger.error(f"Error conectando con auto {auto_id}: {e}")
    
        return None


def plan_info_extractor(plan: Dict, auto_id: str):
    """Extrae mensualidaes, enganche, tasa y seguro del plan que se le pase."""
    
    info = {'plazo': None, 'enganche': None, 'tasa_interes': None, 'seguro': None}

    try:
        info['plazo'] = plan['installments']
        info['enganche'] = plan['value']
        info['tasa_interes'] = plan['rate']

        if plan['insurance']:
            info['seguro'] = plan['insurance']['installmentAmount']

    except Exception as e:
        logger.error("Sucedio un error extrayendo los planes del auto: %s. Error: %s", auto_id, e)
    return info


def upfront_info_extractor(inputData: Dict[str, Any], auto_id: str) -> Optional[Tuple[int, int, int]]:
    """Extrae el valor del enganche simulado, el enganche minimo y enganche maximo"""
    try:
        value = inputData['value']
        min_upfront_value = inputData['min']
        max_upfront_value = inputData['max']
        return value, min_upfront_value, max_upfront_value
    
    except Exception as e:
        logger.error("Sucedio un error extrayendo los enganches del auto: %s. Error: %s", auto_id, e)
        return None


def extract_financial_info(auto_id: str, paymentPlans: Dict[str, Any], inputData: Dict[str, Any], price: int) -> Optional[List]:
    """Maneja plan_info_extractor() y upfront_info_extractor() 
        para obtener la info de los planes y el enganche y devuelve todo en una lista de diccionarios."""

    upfront_data =  upfront_info_extractor(inputData, auto_id)
    if not upfront_data:
        return []
    
    value, min_upfront_value, max_upfront_value = upfront_data

    return [
        {
            'id_auto': auto_id,
            'precio': price,
            'tasa_servicio': round(float(price) * 0.05),

            'plazo': plans_info['plazo'],
            'mensualidad': plans_info['enganche'], 
            'tasa_interes': plans_info['tasa_interes'], 
            'seguro': plans_info['seguro'],
            'enganche_simulado': value, 
            'enganche_min': min_upfront_value, 
            'enganche_max': max_upfront_value
        }
        for plan in paymentPlans
        if (plans_info := plan_info_extractor(plan, auto_id)) and plans_info['plazo']]


def save_batch_to_db(batch_data: List, db_session: Session) -> None:
    """Maneja los batches para su guardado cuando se supera el BATCH_SIZE definido como limite."""
    if not batch_data:
        return
    try:
        db_session.add_all(batch_data)
        db_session.commit()
    except Exception as e:
        logger.error("Error al intentar guardar los datos del batch: %s", e)


def load_financial_plan(car_id: str, plan: Dict) -> Optional[FinancialPlan]:
    """
    Toma el diccionario crudo del JSON, intenta instanciar el plan financiero de SQLModel.
    Si faltan datos o hay un error de validación, lo registra y devuelve None.
    """
    try:
        new_plan = FinancialPlan(
            **plan
        )
        return new_plan
    except ValidationError as e:
        logger.warning("El auto con id: %s tiene los datos incompletos o corruptos: %s", car_id, e)



def load_new_car(car: Dict) -> Optional[Auto]:
    """
    Toma el diccionario crudo del JSON, intenta instanciar el plan financiero de SQLModel.
    Si faltan datos o hay un error de validación, lo registra y devuelve None.
    """
    try:
        new_car = Auto(
            **car
        )
        return new_car
    
    except ValidationError as e:
        logger.warning("El auto con id: %s tiene los datos incompletos o corruptos: %s", car['id'], e)


def main():
    #Aseguramos que la DDBB exista
    create_db_n_tables()

    batch_buffer = []
    raw_json_path = get_raw_json_path()
    current_session = get_fresh_session()
    logger.info("Sesion inical creada.")
    
    with open(raw_json_path, 'r', encoding='utf-8') as f, Session(engine) as db_session:
        for i, line in enumerate(f):
            if i>=5:
                logger.info("Smoke test finalizado. Deteniendo ejecucion")
                break

            # Maneja la sesion para no quemarla
            if i > 0 and i % 50 == 0:
                logger.info("Renovando sesion y limpiando rastros (Auto #%s)", i)
                current_session.close()
                time.sleep(2)
                current_session = get_fresh_session()

            # Checks data car integrity            
            car_json = json.loads(line)
            car_temporal = load_new_car(car_json)
            if not car_temporal:
                continue

            car_db = db_session.get(Auto, car_temporal.id)
            if car_db:
                car_db.price = car_temporal.price
                car_db.km = car_temporal.km
                car_db.discount_offer = car_temporal.discount_offer

                auto_oficial = car_db
            else: # Si el NO auto existe
                auto_oficial = car_temporal


            # Idempotencia: revisamos si el auto ya ha sido procesado hoy
            statement = select(FinancialPlan).where(
                FinancialPlan.id_auto == auto_oficial.id,
                FinancialPlan.fecha_captura == date.today()
            )
            if db_session.exec(statement).first():
                continue

            if auto_oficial.price:
                # Comenzamos la extraccion de datos financieros
                logger.info("%s Extrayendo datos para el ID: %s, %s, %s", i, auto_oficial.id, auto_oficial.slug, auto_oficial.price)
                time.sleep(random.uniform(1.5, 4)) # Simulamos una demora antes de cada request a la API
                response = api_requester(auto_oficial.id, auto_oficial.slug, auto_oficial.price, session=current_session)
                
                if response is None:
                    logger.error("No se obtuvo respuesta del servidor en el auto con ID: %s", auto_oficial.id)
                    continue

                data_json = response.json()
                if 'offers' in data_json:
                    try:
                        paymentPlans = data_json['offers']['paymentPlan']['paymentOptions']['UPFRONT_VALUE']
                        inputData = data_json['offers']['inputData']

                        planes_extraidos = extract_financial_info(auto_oficial.id, paymentPlans, inputData, auto_oficial.price)
                        for plan in planes_extraidos:
                            new_plan = load_financial_plan(auto_oficial.id, plan)
                            auto_oficial.planes.append(new_plan)

                    except Exception as e:
                        logger.warning("No se encontro un llave para el carro: %s. Error: %s", auto_oficial.id, e)
                        continue

                else: 
                    logger.warning("Auto no disponible: %s", auto_oficial.id)
                    continue

            batch_buffer.append(auto_oficial)

            if len(batch_buffer) >= BATCH_SIZE:
                logger.info("Buffer lleno %s registros). Guardando batch...", len(batch_buffer))
                save_batch_to_db(batch_buffer, db_session)
                batch_buffer.clear()
            
        if batch_buffer:
            logger.info("Guardando últimos registros pendientes...")
            save_batch_to_db(batch_buffer, db_session)
            logger.info("Proceso Terminado...")


if __name__ == '__main__':
    main()