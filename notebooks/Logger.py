import logging
from settings import LOGGING_DIR
from pathlib import Path

def setup_logging():
    log_path = Path(LOGGING_DIR) / "pipeline.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.FileHandler(log_path, encoding='utf-8')]
    )