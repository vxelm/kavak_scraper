import requests
from bs4 import BeautifulSoup
import time
import random

# CONFIGURACIÓN
BASE_URL = "https://www.kavak.com/mx/seminuevos"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'es-MX,es;q=0.9'
}

def get_car_urls(max_pages=1):
    all_urls = []
    
    print(f"🕷️ Iniciando crawler para {max_pages} páginas...")

    for page in range(max_pages):
        # Construimos la URL de la página actual
        # Nota: Kavak usa page=0 para la primera, page=1 para la segunda, etc.
        target_url = f"{BASE_URL}?page={page}"
        
        print(f"\n📄 Procesando Página {page + 1}: {target_url}")
        
        try:
            response = requests.get(target_url, headers=HEADERS, timeout=10)
            
            if response.status_code != 200:
                print(f"⛔ Error {response.status_code} en página {page}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # ESTRATEGIA DE SELECCIÓN ROBUSTA:
            # Buscamos etiquetas 'a' donde 'data-testid' empiece con 'card-product'
            cards = soup.find_all('a', attrs={'data-testid': lambda x: x and x.startswith('card-product')})
            
            print(f"   ✅ Encontrados {len(cards)} autos en esta página.")

            for card in cards:
                url = card.get('href')
                if url:
                    # A veces vienen relativas (/usado/...), a veces absolutas. Normalizamos.
                    if not url.startswith('http'):
                        url = "https://www.kavak.com" + url
                    all_urls.append(url)

            # ANTI-BOT: Espera aleatoria entre 2 y 5 segundos
            sleep_time = random.uniform(2, 5)
            print(f"   💤 Durmiendo {sleep_time:.2f} segundos...")
            time.sleep(sleep_time)

        except Exception as e:
            print(f"💥 Error crítico: {e}")

    return all_urls

if __name__ == "__main__":
    # Probamos con 2 páginas para verificar
    links = get_car_urls(max_pages=2)
    
    print(f"\n🏁 RASTREO FINALIZADO.")
    print(f"Total de URLs recolectadas: {len(links)}")
    
    # Mostramos las primeras 3 para validar
    print("Ejemplos:")
    for link in links[:3]:
        print(f" - {link}")