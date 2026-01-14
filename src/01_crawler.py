
import requests
import random
import time
import os
import settings
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Configuracion
#BASE_URL = "https://www.kavak.com/mx/seminuevos"
current_time = datetime.now().strftime('%Y_%m_%d-%Hh_%Mm')
PATH_TO_SAVE = f"../data/raw/raw_html/{current_time}/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'es-MX,es;q=0.9'
}
os.makedirs(PATH_TO_SAVE, exist_ok=True)


def get_raw_data(url, page, path):
    """Obtiene el HTML y lo guarda para cada pagina que se le pase."""
    try:
        time.sleep(random.uniform(1, 3))
        response = requests.get(f"{url}?page={page}", headers=HEADERS, timeout=20)
        
        if response.status_code == 200:
            #current_time = datetime.now().strftime('%Y_%m_%d-%Hh_%Mm')
            #filename = f"{path}pagina_{page}_{current_time}.html"
            filename = f"{path}pagina_{page}.html"

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(response.text)
                
            return f"✅ Página {page} guardada correctamente en {filename}"
        else:
            return f"Warning: La pagina {page} devolvio status {response.status_code}"            
        
    except Exception as e:
        return f"Sucedio un error {e} tratando de descargar la pagina numero: {page}"


def main(start, end):
    print(f"Iniciando crawler concurrente de pag {start} a {end}...")
    futures = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        for page in range(start, end + 1):
            future = executor.submit(get_raw_data, BASE_URL, page, PATH_TO_SAVE)
            futures.append(future)
    
    for future in futures:
        #.result() BLOQUEA hasta que este hilo especifico termine
        # y devuelve lo que hizo el 'return' de get_raw_data()
        try:
            print(future.result())
        except Exception as e:
            print(f"Hilo fallido: {e}")


if __name__ == "__main__":
    main(start=1, end=222)


