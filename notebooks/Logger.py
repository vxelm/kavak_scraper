import logging
from settings import LOGGING_DIR
from pathlib import Path
from datetime import datetime
from glob import glob

def get_last_log():
    

def setup_logging():
    timestamp = datetime.now().strftime('%Y_%m_%d-%Hh_%Mm')
    log_filename = f"logs_{timestamp}.log"
    log_path = Path(LOGGING_DIR) / filename
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(module)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.FileHandler(log_path, encoding='utf-8')]
    )