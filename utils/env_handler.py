import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def _base_dir() -> Path:
    """
    Devuelve el directorio raíz del proyecto.
    - Script normal: directorio padre de utils/
    - Ejecutable PyInstaller: directorio donde está el .exe
    """
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def _bundle_dir() -> Path:
    """
    Directorio donde PyInstaller extrae los archivos de datos empaquetados.
    En modo normal coincide con _base_dir().
    """
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def get_config():
    base = _base_dir()
    env_path = base / "config" / ".env"

    if not env_path.exists():
        raise FileNotFoundError(
            f"No se encontró config/.env en: {env_path}\n"
            f"Copia config/.env.example a config/.env y completa las credenciales."
        )

    load_dotenv(env_path)

    return {
        "server": {
            "host": os.getenv("SRV_HOST"),
            "port": int(os.getenv("SRV_PORT", 22)),
            "user": os.getenv("SRV_USER"),
            "pass": os.getenv("SRV_PASS"),
        },
        "middleware": {
            "host": os.getenv("MW_HOST", "127.0.0.1"),
            "port": int(os.getenv("MW_PORT", 12002)),
        },
        "equipos": {
            "user": os.getenv("EQUIP_USER", "pi"),
            "pass": os.getenv("EQUIP_PASS", ""),
            "antena_ip": os.getenv("ANTENA_IP", "192.168.19.130"),
            "pantalla_ip": os.getenv("PANTALLA_IP", "192.168.19.100"),
        },
        "win_downloads": os.getenv("WIN_DOWNLOADS"),
    }


def get_param_mapping() -> dict:
    mapping_path = _bundle_dir() / "config" / "param_mapping.json"
    try:
        if mapping_path.exists():
            with open(mapping_path, encoding="utf-8") as f:
                return json.load(f)
        return {}
    except Exception as e:
        from utils.logger import error_logger
        error_logger(f"Error cargando param_mapping.json: {e}")
        return {}
