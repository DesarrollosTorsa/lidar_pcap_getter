#!/usr/bin/env python3
"""
main.py — Orquestación de captura LiDAR desde equipos (Antapaccay)

Flujo: WSL Local → Servidor Antapaccay → Concentrador CM (localhost:CONC_PORT)

Puerto del concentrador (calculado automáticamente):
    - Ligero con ID de 3 dígitos  → 12000 + ID_num  (ej. LV181 → 12181)
    - Todos los demás              → ID_num           (ej. S2160 → 2160, LV1985 → 1985)

Uso (captura única):
    python main.py 15000 S2160:RIGHT

Uso (batch compacto — varias posiciones por equipo, varios equipos):
    python main.py 15000 S2051:LEFT,REAR,RIGHT S2160:REAR,RIGHT S2162:LEFT,RIGHT

Uso (batch por archivo JSON):
    python main.py 15000 --batch captures.json

Formato captures.json:
    [
      {"equipo": "S2051", "positions": ["LEFT", "REAR", "RIGHT"]},
      {"equipo": "S2160", "positions": ["REAR", "RIGHT"]}
    ]

Flags:
    --override      Sobreescribe archivos existentes sin preguntar
    --solo-captura  Dispara la captura pero no descarga el zip
"""

import argparse
import json
import re
import shutil
import sys
import time
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

from utils.env_handler import get_config
from utils.logger import info_logger, error_logger, warning_logger
from conexion.ssh_manager import crear_cliente_ssh, conectar_ssh, conectar_con_salto, cerrar_ssh

def _bundle_dir() -> Path:
    """Directorio con archivos de datos (funciona en script normal y en exe PyInstaller)."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


def _exe_dir() -> Path:
    """Directorio donde vive el ejecutable o el script."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


FLEET_PATH = _bundle_dir() / "data" / "fleet_info.json"
DESCARGAS_BASE = _exe_dir() / "descargas"
REMOTE_BASE = "/tmp/LidarDataRaw"
NC_PORT = 12001


def get_descargas_dir() -> Path:
    """Devuelve ./descargas/YYYYMMDD/, creándola si no existe."""
    dated = DESCARGAS_BASE / datetime.now().strftime("%Y%m%d")
    dated.mkdir(parents=True, exist_ok=True)
    return dated


# ── Fleet / equipo helpers ────────────────────────────────────────────────────

def cargar_flota() -> dict:
    with open(FLEET_PATH, encoding="utf-8") as f:
        return json.load(f)


def resolver_equipo(equipo_input: str) -> tuple[str, str]:
    """Devuelve (id_num, categoria). Lanza ValueError si no existe en la flota."""
    fleet = cargar_flota()
    clean = equipo_input.strip().upper()
    if clean not in fleet:
        raise ValueError(f"'{equipo_input}' no encontrado en fleet_info.json")
    id_num = re.sub(r"\D", "", clean)
    return id_num, fleet[clean]


def calcular_conc_port(id_num: str, categoria: str) -> int:
    num = int(id_num)
    if categoria == "Ligero" and len(id_num) == 3:
        return 12000 + num
    return num


# ── Nombre / comando ──────────────────────────────────────────────────────────

def construir_nombre(id_num: str, position: str) -> str:
    fecha = datetime.now().strftime("%Y%m%d")
    return f"{id_num}_{position}_{fecha}"


def construir_comando_nc(nombre: str, position: str, duration_ms: int) -> str:
    payload = (
        f"SAVE_LIDAR_DATA_RAW="
        f"ENABLE:TRUE,"
        f"NAME:{nombre},"
        f"SPLIT_PATHS:FALSE,"
        f"ALL_DATA:TRUE,"
        f"POSITION:{position},"
        f"ZIP_DATA:TRUE,"
        f"TIME_SAVE:{duration_ms},"
        f"TCP_DUMP_SAVE:TRUE;"
    )
    return f'echo "{payload}" | nc -N 127.0.0.1 {NC_PORT}'


# ── SSH helpers ───────────────────────────────────────────────────────────────

def abrir_conexion(cfg: dict, conc_port: int):
    """Abre la cadena SSH hasta el Concentrador. Devuelve (ssh_srv, ssh_conc)."""
    ssh_srv = crear_cliente_ssh()
    conectar_ssh(
        ssh_srv,
        hostname=cfg["server"]["host"],
        port=cfg["server"]["port"],
        username=cfg["server"]["user"],
        password=cfg["server"]["pass"],
        timeout=30,
    )
    ssh_srv.get_transport().set_keepalive(30)
    info_logger("OK — Servidor Antapaccay")

    ssh_conc = conectar_con_salto(
        ssh_srv,
        target_host="localhost",
        target_port=conc_port,
        user=cfg["equipos"]["user"],
        password=cfg["equipos"]["pass"],
    )
    ssh_conc.get_transport().set_keepalive(30)
    info_logger(f"OK — Concentrador CM (puerto {conc_port})")
    return ssh_srv, ssh_conc


def ejecutar_comando(ssh_conc, comando: str) -> None:
    info_logger(f"Ejecutando: {comando}")
    _, stdout, stderr = ssh_conc.exec_command(comando)
    salida = stdout.read().decode().strip()
    errores = stderr.read().decode().strip()
    if salida:
        info_logger(f"stdout: {salida}")
    if errores:
        warning_logger(f"stderr: {errores}")


# ── Verificación de existencia ────────────────────────────────────────────────

def verificar_existencia(ssh_conc, nombre: str) -> tuple[bool, str]:
    """
    Comprueba si /tmp/LidarDataRaw/<nombre>.zip existe en el Concentrador.
    Devuelve (existe: bool, detalle_ls: str).
    """
    remote_path = f"{REMOTE_BASE}/{nombre}.zip"
    _, stdout, _ = ssh_conc.exec_command(f"ls -la {remote_path} 2>/dev/null")
    info = stdout.read().decode().strip()
    return bool(info), info


def preguntar_accion_existente(nombre: str, ls_info: str) -> str:
    """
    Muestra info del archivo existente y pregunta qué hacer.
    Devuelve: 'override' | 'download' | 'skip'
    """
    print(f"\n  [!] Ya existe: {nombre}.zip")
    print(f"      {ls_info}")
    print("      Opciones: [s] Re-capturar y sobreescribir  [d] Descargar el existente  [N] Saltar")
    respuesta = input("      ¿Qué hacer? [s/d/N]: ").strip().lower()
    if respuesta == "s":
        return "override"
    if respuesta == "d":
        return "download"
    return "skip"


# ── Descarga ──────────────────────────────────────────────────────────────────

def listar_lidar_raw(ssh_conc) -> str:
    """Lista /tmp/LidarDataRaw/ y devuelve el contenido como string."""
    _, stdout, _ = ssh_conc.exec_command(f"ls -lah {REMOTE_BASE}/ 2>/dev/null")
    return stdout.read().decode().strip()


def descargar_zip(ssh_conc, nombre: str, descargas_dir: Path, win_downloads: str | None) -> Path:
    remote_path = f"{REMOTE_BASE}/{nombre}.zip"
    local_path = descargas_dir / f"{nombre}.zip"

    info_logger(f"Descargando {remote_path} → {local_path}")
    sftp = ssh_conc.open_sftp()
    try:
        sftp.get(remote_path, str(local_path))
    finally:
        sftp.close()

    size_mb = local_path.stat().st_size / 1_048_576
    info_logger(f"OK — {local_path.name}  ({size_mb:.1f} MB)")

    if win_downloads:
        win_dir = Path(win_downloads) / descargas_dir.name  # misma subcarpeta con fecha
        win_dir.mkdir(parents=True, exist_ok=True)
        win_path = win_dir / local_path.name
        shutil.copy2(local_path, win_path)
        info_logger(f"Copiado a Windows: {win_path}")

    return local_path


# ── Parseo de targets ─────────────────────────────────────────────────────────

def parsear_targets_inline(raw: list[str]) -> list[tuple[str, str]]:
    """
    Acepta dos formatos:
      - Compacto:  'S2051:LEFT,REAR,RIGHT'  → tres tuplas para S2051
      - Simple:    'S2051:LEFT'             → una tupla
    Devuelve lista de (equipo, position).
    """
    POSICIONES_VALIDAS = {"LEFT", "RIGHT", "REAR"}
    targets = []
    for item in raw:
        parts = item.upper().split(":")
        if len(parts) != 2:
            raise ValueError(f"Formato inválido '{item}'. Usar EQUIPO:POS o EQUIPO:POS1,POS2")
        equipo = parts[0]
        posiciones = [p.strip() for p in parts[1].split(",")]
        invalidas = [p for p in posiciones if p not in POSICIONES_VALIDAS]
        if invalidas:
            raise ValueError(f"Posicion(es) no válida(s): {invalidas}. Opciones: LEFT, RIGHT, REAR")
        for pos in posiciones:
            targets.append((equipo, pos))
    return targets


def parsear_batch_json(path: str) -> list[tuple[str, str]]:
    """Carga captures.json y devuelve lista de (equipo, position)."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    targets = []
    for entry in data:
        equipo = entry["equipo"].upper()
        for pos in entry["positions"]:
            targets.append((equipo, pos.upper()))
    return targets


def agrupar_por_equipo(targets: list[tuple[str, str]]) -> OrderedDict:
    """Agrupa preservando el orden de aparición: {equipo_id: [pos, ...]}"""
    grupos = OrderedDict()
    for equipo, pos in targets:
        grupos.setdefault(equipo, []).append(pos)
    return grupos


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Captura datos LiDAR desde equipos (Antapaccay)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ejemplos:\n"
            "  python main.py 15000 S2160:RIGHT\n"
            "  python main.py 15000 S2051:LEFT,REAR,RIGHT S2160:REAR,RIGHT\n"
            "  python main.py 15000 --batch captures.json\n"
            "  python main.py 15000 S2051:LEFT,REAR,RIGHT --override\n"
        ),
    )
    parser.add_argument("duration_ms", type=int, help="Duración de captura en milisegundos")
    parser.add_argument(
        "targets",
        nargs="*",
        metavar="EQUIPO:POS[,POS2,...]",
        help="Targets en formato compacto: S2051:LEFT,REAR,RIGHT  o  S2160:RIGHT",
    )
    parser.add_argument("--batch", metavar="FILE", help="Archivo JSON con lista de capturas")
    parser.add_argument(
        "--override",
        action="store_true",
        help="Sobreescribe archivos existentes sin preguntar",
    )
    parser.add_argument(
        "--solo-captura",
        action="store_true",
        help="Dispara la captura pero no descarga el zip",
    )
    return parser.parse_args()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()
    cfg = get_config()

    # Construir lista de targets
    try:
        if args.batch:
            targets = parsear_batch_json(args.batch)
        elif args.targets:
            targets = parsear_targets_inline(args.targets)
        else:
            error_logger("Debes indicar al menos un target (EQUIPO:POSICION) o --batch FILE")
            sys.exit(1)
    except Exception as e:
        error_logger(f"Error parseando targets: {e}")
        sys.exit(1)

    grupos = agrupar_por_equipo(targets)
    total = sum(len(v) for v in grupos.values())

    descargas_dir = get_descargas_dir()
    win_downloads = cfg.get("win_downloads")

    info_logger("=" * 55)
    info_logger(f"Batch: {total} captura(s) en {len(grupos)} equipo(s)")
    info_logger(f"Duracion por captura: {args.duration_ms} ms  ({args.duration_ms / 1000:.1f} s)")
    info_logger(f"Destino local  : {descargas_dir}")
    if win_downloads:
        info_logger(f"Destino Windows: {win_downloads}/{descargas_dir.name}/")
    if args.override:
        info_logger("Modo --override activo: se sobreescribiran archivos existentes")
    info_logger("=" * 55)

    # Resultados para el resumen final
    resultados = []  # (nombre, estado, detalle)

    for equipo_id, posiciones in grupos.items():
        try:
            id_num, categoria = resolver_equipo(equipo_id)
        except ValueError as e:
            error_logger(str(e))
            for pos in posiciones:
                nombre = construir_nombre(re.sub(r"\D", "", equipo_id), pos)
                resultados.append((nombre, "ERROR", str(e)))
            continue

        conc_port = calcular_conc_port(id_num, categoria)

        info_logger("-" * 55)
        info_logger(f"Equipo: {equipo_id}  ({categoria})  |  ID: {id_num}  |  Puerto conc.: {conc_port}")
        info_logger(f"Posiciones: {', '.join(posiciones)}")

        ssh_srv = ssh_conc = None
        try:
            info_logger("Conectando...")
            ssh_srv, ssh_conc = abrir_conexion(cfg, conc_port)

            for pos in posiciones:
                nombre = construir_nombre(id_num, pos)
                info_logger(f"  >> {nombre}")

                # [CHECK 1] Verificar existencia previa antes de capturar
                existe, ls_info = verificar_existencia(ssh_conc, nombre)
                if existe:
                    if args.override:
                        warning_logger(f"  [CHECK 1] Archivo ya existe (override activo): {ls_info}")
                        # sigue al bloque de captura
                    else:
                        accion = preguntar_accion_existente(nombre, ls_info)
                        if accion == "skip":
                            info_logger(f"  Saltado por el usuario.")
                            resultados.append((nombre, "SALTADO", ls_info))
                            continue
                        elif accion == "download":
                            info_logger(f"  Descargando archivo existente sin re-capturar...")
                            try:
                                local_path = descargar_zip(ssh_conc, nombre, descargas_dir, win_downloads)
                                size_mb = local_path.stat().st_size / 1_048_576
                                resultados.append((nombre, "OK", f"{size_mb:.1f} MB (existente)"))
                            except Exception as e:
                                error_logger(f"  Error descargando {nombre}: {e}")
                                resultados.append((nombre, "ERROR-DESCARGA", str(e)))
                            continue
                        # accion == "override": sigue al bloque de captura
                else:
                    info_logger(f"  [CHECK 1] No existe previamente — OK para capturar")

                # Disparar captura
                comando_nc = construir_comando_nc(nombre, pos, args.duration_ms)
                ejecutar_comando(ssh_conc, comando_nc)
                info_logger(f"  Captura iniciada. Esperando {args.duration_ms / 1000:.1f} s...")
                time.sleep(args.duration_ms / 1000 + 7)  # espera un poco más para asegurar que el zip se genere

                # [CHECK 2] Verificar que el archivo apareció tras la espera
                existe_post, ls_post = verificar_existencia(ssh_conc, nombre)
                if existe_post:
                    info_logger(f"  [CHECK 2] Archivo presente: {ls_post}")
                else:
                    contenido_dir = listar_lidar_raw(ssh_conc)
                    warning_logger(
                        f"  [CHECK 2] Archivo NO encontrado tras la espera.\n"
                        f"  Contenido de {REMOTE_BASE}/:\n{contenido_dir}"
                    )
                    resultados.append((nombre, "NO-GENERADO", "archivo ausente tras espera"))
                    continue

                if args.solo_captura:
                    info_logger("  Modo --solo-captura: descarga omitida.")
                    resultados.append((nombre, "SOLO-CAPTURA", ""))
                else:
                    try:
                        local_path = descargar_zip(ssh_conc, nombre, descargas_dir, win_downloads)
                        size_mb = local_path.stat().st_size / 1_048_576
                        resultados.append((nombre, "OK", f"{size_mb:.1f} MB"))
                    except Exception as e:
                        error_logger(f"  Error descargando {nombre}: {e}")
                        resultados.append((nombre, "ERROR-DESCARGA", str(e)))

        except Exception as e:
            error_logger(f"Error de conexion para {equipo_id}: {e}")
            for pos in posiciones:
                nombre = construir_nombre(id_num, pos)
                resultados.append((nombre, "ERROR-CONEXION", str(e)))
        finally:
            cerrar_ssh(ssh_conc)
            cerrar_ssh(ssh_srv)

    # Resumen final
    info_logger("=" * 55)
    info_logger("RESUMEN")
    info_logger("=" * 55)
    for nombre, estado, detalle in resultados:
        linea = f"  [{estado:<15}]  {nombre}.zip"
        if detalle and estado in ("OK", "SALTADO"):
            linea += f"  —  {detalle}"
        info_logger(linea)
    info_logger("=" * 55)


if __name__ == "__main__":
    main()
