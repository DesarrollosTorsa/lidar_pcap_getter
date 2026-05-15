import os
from pathlib import Path
from dotenv import load_dotenv
import json

# Ubicación dinámica: UtilitiesToolboxV2/config/.env
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / "config" / ".env"

def get_config():
    if not ENV_PATH.exists():
        raise FileNotFoundError(f"No se encontró el .env en {ENV_PATH}")
    
    load_dotenv(ENV_PATH)
    
    return {
        "server": {
            "host": os.getenv("SRV_HOST"),
            "port": int(os.getenv("SRV_PORT", 22)),
            "user": os.getenv("SRV_USER"),
            "pass": os.getenv("SRV_PASS")
        },
        "middleware": {
            "host": os.getenv("MW_HOST", "127.0.0.1"),
            "port": int(os.getenv("MW_PORT", 12002))
        },
        "equipos": {
            "user": os.getenv("EQUIP_USER", "pi"),
            "pass": os.getenv("EQUIP_PASS", "Tors42018"),
            "antena_ip": os.getenv("ANTENA_IP", "192.168.19.130"),
            "pantalla_ip": os.getenv("PANTALLA_IP", "192.168.19.100")
        },
        "win_downloads": os.getenv("WIN_DOWNLOADS")
    }

import json

def get_param_mapping():
    """Carga el mapeo de parámetros técnicos a etiquetas legibles."""
    mapping_path = BASE_DIR / "config" / "param_mapping.json"
    try:
        if mapping_path.exists():
            with open(mapping_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        from utils.logger import error_logger
        error_logger(f"Error cargando param_mapping.json: {e}")
        return {}