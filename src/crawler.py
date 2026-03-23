import logging
import settings
import requests
import random
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from datetime import datetime
from typing import Optional
from logger import setup_logging


setup_logging()
logger = logging.getLogger(__name__)

thread_local = threading.local()


def get_session() -> requests.Session:
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session


def generate_filepath(base_path: str, page_num: int) -> str:
    return os.path.join(base_path, f"pagina_{page_num}.html")


def save_to_disk(filepath: str, content: str) -> None:
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info("Guardado: %s", filepath)
    
    except Exception as e:
        logger.error("Error escribiendo en disco %s: %s", filepath, e)
        raise


def download_page(session: requests.Session, url: str, page_num: int) -> Optional[str]:
    target_url = f"{url}?page={page_num}"
    try:
        time.sleep(random.uniform(1,3))

        response = session.get(
            target_url,
            headers={'User-Agent': random.choice(settings.USER_AGENTS)},
            timeout=10
        )
        response.raise_for_status()
        
        return response.text

    except Exception as e:
        logger.warning("Fallo descarga pagina %s: %s", page_num, e)
        return None



def process_page_workflow(page_num: int, save_dir: str) -> None:
    filepath = generate_filepath(save_dir, page_num)

    if os.path.exists(filepath):
        logger.info("Pagina %s ya existe, Saltando", page_num)
        return
    
    session = get_session()
    html_content = download_page(session=session, url=settings.BASE_URL, page_num=page_num)

    if html_content:
        save_to_disk(filepath, html_content)


def main(start, end):
    # Configuracion
    TIMESTAMP = datetime.now().strftime('%Y_%m_%d-%Hh_%Mm')
    save_dir = os.path.join(settings.RAW_HTML_DIR, TIMESTAMP)
    os.makedirs(save_dir, exist_ok=True)

    logger.info("Iniciando crawler concurrente de pag %s a %s...", start, end)
    
    futures = []
    with ThreadPoolExecutor(max_workers=settings.MAX_WORKERS) as executor:
        for page in range(start, end + 1):
            logger.info("Descargando pagina %s", page)
            try:
                future = executor.submit(process_page_workflow, page, save_dir)
                futures.append(future)
            except Exception as e:
                logger.error("Sucedio un error: %s", e)        

    for future in as_completed(futures):
        try:
            result = future.result()
            #logger.info("Resultado: %s", result)
        except Exception as e:
            logger.error("Un hilo genero una excepcion: %s", e)



if __name__ == "__main__":
    if not hasattr(settings, 'BASE_URL'):
        logging.critical("Falta BASE_URL en settings.py")

    else:
        main(start=1, end=2)


