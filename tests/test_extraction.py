import requests
from bs4 import BeautifulSoup
import json
import time

# URL de prueba (Busca una URL real de un auto en Kavak y pégala aquí)
TEST_URL = "https://www.kavak.com/mx/usado/kia-forte-20_sx_at-sedan-2017?id=463489"

# 1. Headers: Fundamental para que no nos bloqueen de inmediato.
# Fingimos ser un navegador Chrome real.
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'es-MX,es;q=0.9'
}

def extract_car_data(url):
    print(f"🔌 Conectando a: {url}")
    
    try:
        # Hacemos la petición GET
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        # Check de estado (Best Practice)
        if response.status_code != 200:
            print(f"Error: Código de estado {response.status_code}")
            return None

        # Parseamos el HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # --- TU TAREA AQUÍ ---
        # Localiza el script que encontraste: id="vip-snippet"
        # script_tag = soup.find( ... ) completalo
        script_tag = soup.find('script', {'id': 'vip-snippet', 'type': 'application/ld+json'})

        if not script_tag:
            print("❌ No se encontró el script JSON-LD. ¿Kavak cambió el ID?")
            return None

        # Extraemos el contenido de texto del script y lo convertimos a Diccionario Python
        json_text = script_tag.string
        data = json.loads(json_text)
        
        return data

    except Exception as e:
        print(f"💥 Excepción fatal: {e}")
        return None

if __name__ == "__main__":
    data = extract_car_data(TEST_URL)
    if data:
        print("✅ Datos extraídos con éxito:")
        # Imprimimos bonito (Pretty Print)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("💀 Falló la extracción.")