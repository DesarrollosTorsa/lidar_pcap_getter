#logger.py
import logging
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent.parent / "data" / "session.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_PATH, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

#formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s - Debido a:%(pathname)s:%(lineno)d')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s ')

file_handler = logging.FileHandler('registro.log', mode='w', encoding='utf-8')
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
    
if __name__ == "__main__":
    info_logger("Logger configurado correctamente")
    warning_logger("Este es un mensaje de advertencia")
    error_logger("Este es un mensaje de error")
    critical_logger("Este es un mensaje crítico")
