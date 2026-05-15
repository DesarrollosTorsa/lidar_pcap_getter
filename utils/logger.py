# logger.py
import logging
import sys
from pathlib import Path


def _base_dir() -> Path:
    """Directorio raíz del proyecto, funciona en script normal y en exe PyInstaller."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = _base_dir()

# Crear carpeta data/ si no existe (necesario en el exe)
(BASE_DIR / "data").mkdir(exist_ok=True)

LOG_PATH = BASE_DIR / "data" / "session.log"
REGISTRO_PATH = BASE_DIR / "registro.log"

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger("lidar_pcap_getter")
logger.setLevel(logging.INFO)

if not logger.handlers:
    file_handler = logging.FileHandler(REGISTRO_PATH, mode='a', encoding='utf-8')
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def info_logger(message) -> None:
    logger.info(message)

def warning_logger(message) -> None:
    logger.warning(message)

def error_logger(message) -> None:
    logger.error(message)

def critical_logger(message) -> None:
    logger.critical(message)
