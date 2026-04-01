from concurrent.futures import ThreadPoolExecutor, as_completed
from src.logger import setup_logging
from src import settings
from datetime import datetime
from typing import Optional

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


from pathlib import Path
import threading
import requests
import logging
import random
import time

logger = logging.getLogger(__name__)
thread_local = threading.local()


def generate_retry_strategy(total: int = 5, backoff_factor: int = 1) -> Retry:
    """Retorna la estrategia de reintentos"""
    retry_strategy = Retry(
        total = total,
        backoff_factor = backoff_factor,
        status_forcelist = [429, 500, 502, 503, 504],
        allowed_methods = ["HEAD", "GET"]
    )

    return retry_strategy

def get_session() -> requests.Session:
    if not hasattr(thread_local, "session"):
        session = requests.Session()
        retry_strategy = generate_retry_strategy()
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        thread_local.session = session
    return thread_local.session



def generate_filepath(base_path: Path, page_num: int) -> Path:
    return base_path / f"pagina_{page_num}.html"



def save_to_disk(filepath: Path, content: str) -> None:
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info("Guardado: %s", filepath)
    
    except Exception as e:
        logger.error("Error escribiendo en disco %s: %s", filepath, e)
        raise




def download_page(session: requests.Session, url: str, page_num: int) -> Optional[str]:
    """Descarga las paginas usando la session creada"""
    target_url = f"{url}?page={page_num}"
    try:
        time.sleep(random.uniform(1,3))

        response = session.get(
            target_url,
            headers={'User-Agent': random.choice(settings.USER_AGENTS)},
            timeout=settings.REQUEST_TIMEOUT
        )
        response.raise_for_status()
        
        return response.text

    except requests.exceptions.RequestException as e:
        logger.warning("Fallo descarga pagina %s: %s", page_num, e)
        return None



def process_page_workflow(page_num: int, save_dir: Path) -> None:
    """Orquesta la session, la descarga y el guardado de la pagina"""
    filepath = generate_filepath(save_dir, page_num)
    logger.info("Descargando pagina numero: %s", page_num)

    if filepath.exists():
        logger.info("Pagina %s ya existe, Saltando", page_num)
        return
    
    session = get_session()
    html_content = download_page(session=session, url=settings.BASE_URL, page_num=page_num)

    if html_content:
        save_to_disk(filepath, html_content)



def main(start: int, end: int) -> None:
    # Configuracion
    TIMESTAMP = datetime.now().strftime('%Y_%m_%d-%Hh_%Mm')
    save_dir = settings.RAW_HTML_DIR / TIMESTAMP
    save_dir.mkdir(parents=True, exist_ok=True)

    # Configurando logger
    setup_logging()

    logger.info("Iniciando crawler concurrente de pag %s a %s...", start, end)
    
    futures = []
    with ThreadPoolExecutor(max_workers=settings.MAX_WORKERS) as executor:
        for page in range(start, end + 1):
            try:
                future = executor.submit(process_page_workflow, page, save_dir)
                futures.append(future)
            except Exception as e:
                logger.error("Sucedio un error: %s", e)        

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error("Un hilo genero una excepcion: %s", e)


if __name__ == "__main__":
    main(start=1, end=205)