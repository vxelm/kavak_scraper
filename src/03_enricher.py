
import os
import json
import time
import random
import requests
import pandas as pd
from glob import glob
from datetime import datetime


# Aseguramos que existan las carpetas antes de guardar
os.makedirs('../config/logs', exist_ok=True)
os.makedirs('../data/processed/csv/financial_data', exist_ok=True)

json_files = glob('../data/processed/json/*.jsonl')
json_files.sort()


# Configuracion
timestamp = datetime.now().strftime('%Y_%m_%d-%Hh_%Mm')
logs_path = f"../config/logs/logs_{timestamp}.log"

csv_path = f"../data/processed/csv/financial_data_{timestamp}.csv"

json_path = json_files[-1]
print(json_path)


# Example: 'https://www.kavak.com/api/vip-ui/mx/calculator/468814?upfront-amount=116499'
FINANCITAL_API = 'https://www.kavak.com/api/vip-ui/mx/calculator'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'es-MX,es;q=0.9'
}


def get_minimum_upfront_amount(price):
    """Retorna el 16% sobre el valor del vehiculo como enganche"""
    return float(price) * 0.16


def get_fresh_session():
    """Crea una sesion nueva, limpiando asi los headers y cookies"""
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def log_writer(message):
    """Maneja los mensajes de registro en a traves de las distintas funciones"""
    timestamp = datetime.now().strftime('%Y_%m_%d-%Hh_%Mm')
    try:
        with open(logs_path, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp} " + message + '\n')
    except Exception as e:
        print(f"No se pudo escribir el log: {e}")


def api_requester(auto_id, headers, price, session):
    """Realiza las peticiones a la API Financiera de Kavak para obtener los distintos planes de financiamiento."""
    api_url = f"{FINANCITAL_API}/{auto_id}"
    upfront_amount = int(get_minimum_upfront_amount(price))
    query_params = {
        'upfront-amount': upfront_amount
    }
    
    try:
        response = session.get(api_url, headers=headers, params=query_params, timeout=10)
        response.raise_for_status()
        return response

    except requests.exceptions.RequestException as e:
        log_writer(f"Error conectando con auto {auto_id}: {e}")
    
        return None


def plan_info_extractor(plan, auto_id):
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
        log_writer(f"Sucedio un error extrayendo los planes del auto: {auto_id}: {e}")
        return None


def upfront_info_extractor(inputData, auto_id):
    """Extrae el valor del enganche simulado, el enganche minimo y enganche maximo"""

    try:
        value = inputData['value']
        min_upfront_value = inputData['min']
        max_upfront_value = inputData['max']
        return value, min_upfront_value, max_upfront_value
    
    except Exception as e:
        log_writer(f"Sucedio un error extrayendo los enganches del auto: {auto_id}: {e}")
        return None


def extract_financial_info(auto_id, paymentPlans, inputData, price):
    """Maneja plan_info_extractor() y upfront_info_extractor() 
        para obtener la info de los planes y el enganche y devuelve todo en una lista de diccionarios."""

    data_plan_list = []

    upfront_data =  upfront_info_extractor(inputData, auto_id)
    if not upfront_data:
        return []
    
    value, min_upfront_value, max_upfront_value = upfront_data

    for plan in paymentPlans:        
        plazo, mensualidad, tasa_interes, seguro = plan_info_extractor(plan, auto_id)      

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


def save_batch_to_csv(batch_data, path):
    """Maneja los batches para su guardado cuando se supera el BATCH_SIZE definido como limite."""
    if not batch_data:
        return
    
    try:
        df = pd.DataFrame(batch_data)
        write_headers = not os.path.exists(path)
        df.to_csv(path, mode='a', index=False, header=write_headers, encoding='utf-8-sig')
        print(f"Batch de {len(batch_data)} filas guardado.")

    except Exception as e:
        log_writer(f"Error al intentar guardar los datos del batch: {e}")


def main():
    batch_buffer = []
    BATCH_SIZE = 10

    current_session = get_fresh_session()
    print("Sesion inical creada.")

    with open(json_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
   
            if i > 0 and i % 50 == 0:
                print(f"Renovando sesion y limiando rastros (Auto #{i})")
                current_session.close()
                time.sleep(2)
                current_session = get_fresh_session()

            car = json.loads(line)
            car_id = car['id']
            slug = car['slug']
            price = car['price']
            print(f"{i} Extrayendo datos para el ID: {car_id}, {slug}, {price}")

            # Definimos el referer y los agregamos a los headers
            referer = slug + "?" + "id=" + car_id
            headers_copy = HEADERS.copy()
            headers_copy['Referer'] = referer

            # Simulamos una demora antes de cada request a la API
            time.sleep(random.uniform(1.5, 4))
            response = api_requester(car_id, headers_copy, price, session=current_session)
            

            if response is None:
                log_writer(f"No se obtuvo respuesta para el auto con ID: {car_id}")
                continue

            
            data_json = response.json()
            if 'offers' in data_json:

                try:
                    paymentPlans = data_json['offers']['paymentPlan']['paymentOptions']['UPFRONT_VALUE']
                    inputData = data_json['offers']['inputData']

                    planes_extraidos = extract_financial_info(car_id, paymentPlans, inputData, price)
                    batch_buffer.extend(planes_extraidos)

                except Exception as e:
                    log_writer(f"No se encontro un llave para el carro: {car_id}: {e}")    
                    continue

            else: 
                print(f"Auto no disponible {car_id}")
                log_writer(f"Auto no disponible {car_id}")
                continue
    
            if len(batch_buffer) >= (BATCH_SIZE * 6):
                print(f"Buffer lleno ({len(batch_buffer)} registros). Guardando batch...")
                save_batch_to_csv(batch_buffer, csv_path)
                batch_buffer = []
            
        if batch_buffer:
            print("Guardando últimos registros pendientes...")
            save_batch_to_csv(batch_buffer, csv_path)
            
            print("Proceso Terminado...")


if __name__ == '__main__':
    main()


