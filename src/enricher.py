import os
import json
import time
import random
import requests
import settings
import pandas as pd
import logging
import sys
from Logger import setup_logging
from glob import glob
from typing import Optional, Tuple, Dict, Set, List, Any
from datetime import datetime


# Configurando logger
setup_logging()
logger = logging.getLogger(__name__)


TIMESTAMP = datetime.now().strftime('%Y_%m_%d-%Hh_%Mm')
CSV_PATH = f"{settings.FINANCIAL_DATA_DIR}/financial_data_{TIMESTAMP}.csv"


# Example: 'https://www.kavak.com/api/vip-ui/mx/calculator/468814?upfront-amount=116499'
FINANCIAL_API = 'https://www.kavak.com/api/vip-ui/mx/calculator'
DEFAULT_HEADERS = {
    'Accept-Language': 'es-MX,es;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
}
BATCH_SIZE = 60 # 6 Registros de planes por cada 10 autos


# Configuracion
def get_json_path() -> Optional[str]:
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
    
    try:
        mensualidades = plan['installments']
        enganche = plan['value']
        tasa_interes = plan['rate']

        if plan['insurance']:
            seguro = plan['insurance']['installmentAmount']
        else: 
            seguro = None
        
        return mensualidades, enganche, tasa_interes, seguro
    
    except Exception as e:
        logger.error("Sucedio un error extrayendo los planes del auto: %s. Error: %s", auto_id, e)
        return None, None, None, None


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

    data_plan_list = []

    upfront_data =  upfront_info_extractor(inputData, auto_id)
    if not upfront_data:
        return []
    
    value, min_upfront_value, max_upfront_value = upfront_data

    for plan in paymentPlans:     
        plans_info = plan_info_extractor(plan, auto_id)
        if not plans_info:
            continue   
        plazo, mensualidad, tasa_interes, seguro = plans_info

        data_dict = {
            'ID_Auto':auto_id,
            'Precio':price,
            'Tasa_Servicio': round(float(price) * 0.05),
            'Plazo':plazo,
            'Mensualidad':mensualidad, 
            'Tasa_Interes':tasa_interes, 
            'Seguro':seguro,
            'Enganche_Simulado':value, 
            'Enganche_Min':min_upfront_value, 
            'Enganche_Max':max_upfront_value
            }

        data_plan_list.append(data_dict)

    return data_plan_list


def save_batch_to_csv(batch_data: List, path: str) -> None:
    """Maneja los batches para su guardado cuando se supera el BATCH_SIZE definido como limite."""
    if not batch_data:
        return
    
    try:
        df = pd.DataFrame(batch_data)
        write_headers = not os.path.exists(path)
        df.to_csv(path, mode='a', index=False, header=write_headers, encoding='utf-8-sig')
        logger.info("Batch de %s filas guardado.", len(batch_data))

    except Exception as e:
        logger.error("Error al intentar guardar los datos del batch: %s", e)


def load_processed_ids(csv_path: str) -> Set:
    if not os.path.exists(csv_path):
        return set()
    
    try:
        df = pd.read_csv(csv_path, usecols=['ID_Auto'])
        return set(df['ID_Auto'].astype(str))
    except Exception as e:
        logger.warning("No se pudo leer historial %s", e)
        return set()


def main():
    batch_buffer = []
    json_path = get_json_path()   
    
    current_session = get_fresh_session()
    logger.info("Sesion inical creada.")
    processed_ids = load_processed_ids(CSV_PATH)

    with open(json_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
               
            if i > 0 and i % 50 == 0:
                logger.info("Renovando sesion y limpiando rastros (Auto #%s)", i)
                current_session.close()
                time.sleep(2)
                current_session = get_fresh_session()

            
            car = json.loads(line)
            try:
                car_id = car['id']
                slug = car['slug']
                price = int(car['price'])
                logger.info("%s Extrayendo datos para el ID: %s, %s, %s", i, car_id, slug, price)

            except KeyError as e:
                logger.error("%s: La linea %s del json no pudo ser cargada", e, i)
                continue
           
            if str(car_id) in processed_ids:
                logger.info("Auto %s ya procesado. Saltando.", car_id)
                continue

            # Simulamos una demora antes de cada request a la API
            time.sleep(random.uniform(1.5, 4))
            response = api_requester(car_id, slug, price, session=current_session)
            

            if response is None:
                logger.error("No se obtuvo respuesta para el auto con ID: %s", car_id)
                continue

            
            data_json = response.json()
            if 'offers' in data_json:

                try:
                    paymentPlans = data_json['offers']['paymentPlan']['paymentOptions']['UPFRONT_VALUE']
                    inputData = data_json['offers']['inputData']

                    planes_extraidos = extract_financial_info(car_id, paymentPlans, inputData, price)
                    batch_buffer.extend(planes_extraidos)

                except Exception as e:
                    logger.warning("No se encontro un llave para el carro: %s. Error: %s", car_id, e)
                    continue

            else: 
                logger.warning("Auto no disponible: %s", car_id)
                continue
    
            if len(batch_buffer) >= BATCH_SIZE:
                logger.info("Buffer lleno %s registros). Guardando batch...", len(batch_buffer))
                save_batch_to_csv(batch_buffer, CSV_PATH)
                batch_buffer = []
            
        if batch_buffer:
            logger.info("Guardando últimos registros pendientes...")
            save_batch_to_csv(batch_buffer, CSV_PATH)
            
            logger.info("Proceso Terminado...")


if __name__ == '__main__':
    main()