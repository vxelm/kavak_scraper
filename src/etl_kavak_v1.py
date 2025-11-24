import requests
from bs4 import BeautifulSoup
import json
import time
import random
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# --- CONFIGURACIÓN ---
BASE_URL = "https://www.kavak.com/mx/seminuevos"
OUTPUT_FILE = "kavak_raw_data.jsonl"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'es-MX,es;q=0.9'
}


def get_robust_session():
    session = requests.Session()
    # Configurar reintentos:
    # total=3: Intenta 3 veces antes de rendirse.
    # backoff_factor=1: Espera 1s, luego 2s, luego 4s (exponencial) entre errores.
    # status_forcelist: Si recibe error 500, 502, 503 o 504, reintenta.
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# Variable global para reutilizar la conexión (TCP Keep-Alive)
http = get_robust_session()

def get_car_urls(page_number):
    """Obtiene las URLs de una página específica"""
    target_url = f"{BASE_URL}?page={page_number}"
    print(f"\n📄 Crawling Página {page_number}: {target_url}")
    
    try:
        #response = requests.get(target_url, headers=HEADERS, timeout=10)
        response = http.get(target_url, headers=HEADERS, timeout=20)

        if response.status_code != 200: return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        cards = soup.find_all('a', attrs={'data-testid': lambda x: x and x.startswith('card-product')})
        
        urls = []
        for card in cards:
            url = card.get('href')
            if url:
                if not url.startswith('http'): url = "https://www.kavak.com" + url
                urls.append(url)
        return urls
    except Exception as e:
        print(f"⚠️ Error en página {page_number}: {e}")
        return []

def extract_car_details(url):
    """Extrae el JSON-LD de un auto específico"""
    try:
        # Pausa pequeña para no saturar al servidor en cada petición
        time.sleep(random.uniform(1, 2)) 
        
        #response = requests.get(url, headers=HEADERS, timeout=10)
        response = http.get(url, headers=HEADERS, timeout=20)
        if response.status_code != 200: return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', {'id': 'vip-snippet', 'type': 'application/ld+json'})
        
        if script_tag:
            return json.loads(script_tag.string)
        return None
    except Exception as e:
        print(f"❌ Error extrayendo {url}: {e}")
        return None

def save_to_jsonl(data, filename):
    """Guarda un diccionario como una línea JSON"""
    with open(filename, 'a', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
        f.write('\n') # Salto de línea crucial para JSONL

# --- ORQUESTADOR PRINCIPAL ---
def run_pipeline(start=1, end=245):
    print(f"🚀 Iniciando Pipeline ETL Kavak...")
    
    total_extracted = 0

    for page in range(start, end + 1):
        # 1. EXTRACT (Discovery)
        urls = get_car_urls(page)
        print(f"   found {len(urls)} autos. Procesando...")
        
        for url in urls:
            print(f"   ⬇️ Extrayendo: {url.split('/')[-1][:30]}...", end="")
            
            # 2. EXTRACT (Details)
            car_data = extract_car_details(url)
            
            if car_data:
                # 3. LOAD (Raw Layer)
                # Agregamos metadata nuestra (Timestamp, URL origen)
                wrapper = {
                    "extracted_at": time.time(),
                    "source_url": url,
                    "raw_data": car_data
                }
                save_to_jsonl(wrapper, OUTPUT_FILE)
                print(" ✅ Guardado.")
                total_extracted += 1
            else:
                print(" 💀 Falló.")

        # Pausa larga entre páginas
        print("💤 Descanso entre páginas...")
        time.sleep(random.uniform(3, 6))

    print(f"\n✨ ÉXITO. {total_extracted} autos guardados en {OUTPUT_FILE}")

if __name__ == "__main__":
    # Probamos con 1 sola página para validar flujo completo
    run_pipeline(start=53, end=54)