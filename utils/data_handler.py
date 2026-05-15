import json
import random
from pathlib import Path
from datetime import datetime, timedelta
import re

CATEGORIAS_FLOTA = {
    # Ligeros
    "LV106": "Ligero", "LV116": "Ligero", "LV117": "Ligero", "LV135": "Ligero",
    "LV156": "Ligero", "LV169": "Ligero", "LV171": "Ligero", "LV173": "Ligero",
    "LV178": "Ligero", "LV179": "Ligero", "LV180": "Ligero", "LV181": "Ligero",
    "LV245": "Ligero", "LV251": "Ligero", "LV275": "Ligero", "EQ1164": "Ligero", "LV1985": "Ligero",
    # Camiones
    "C1060": "Camión", "C076": "Camión", "HT3073": "Camión", "HT3075": "Camión",
    "HT3083": "Camión", "HT3084": "Camión", "HT3085": "Camión", "HT3086": "Camión",
    "HT3087": "Camión", "HT3088": "Camión", "HT3089": "Camión", "HT3090": "Camión",
    "HT3101": "Camión", "HT3102": "Camión", "HT3104": "Camión", "HT3105": "Camión",
    "HT3110": "Camión", "HT3111": "Camión", "HT3112": "Camión", "HT3113": "Camión",
    "HT3114": "Camión", "HT3115": "Camión", "HT3116": "Camión", "HT3117": "Camión",
    "HT3118": "Camión", "HT3120": "Camión", "HT3121": "Camión", "HT3122": "Camión",
    "HT3123": "Camión", "HT3124": "Camión", "HT3125": "Camión", "HT3126": "Camión",
    "HT3127": "Camión", "HT3128": "Camión", "HT3129": "Camión", "HT3130": "Camión",
    "HT3131": "Camión", "HT3132": "Camión", "HT3133": "Camión", "HT3134": "Camión",
    "HT3135": "Camión", "HT3136": "Camión", "HT3137": "Camión", "HT3138": "Camión",
    "HT3139": "Camión", "HT3140": "Camión", "HT3141": "Camión", "HT3142": "Camión",
    "HT3150": "Camión", "HT3151": "Camión", "HT3152": "Camión", "HT3153": "Camión",
    "HT3154": "Camión", "HT3157": "Camión", "HT3158": "Camión", "HT3160": "Camión",
    "HT3161": "Camión", "HT3162": "Camión", "HT3163": "Camión", "HT3164": "Camión",
    "HT3165": "Camión", "HT3166": "Camión", "HT3167": "Camión", "HT3168": "Camión",
    "HT3169": "Camión", "HT3170": "Camión", "HT3171": "Camión", "HT3174": "Camión",
    "HT3175": "Camión", "HT3176": "Camión", "HT3177": "Camión", "HT3178": "Camión",
    "HT3179": "Camión", "HT3180": "Camión", "HT3191": "Camión", "HT3192": "Camión",
    "HT3193": "Camión", "HT3194": "Camión", "HT3195": "Camión", "HT3196": "Camión",
    "HT3197": "Camión", "HT3198": "Camión",
    # Palas
    "S2050": "Pala", "S2051": "Pala", "S2160": "Pala", "S2161": "Pala",
    "S2162": "Pala", "S2163": "Pala", "S2164": "Pala", "S2170": "Pala",
    # Auxiliares (El resto según tu regla)
    "5029": "Auxiliar", "5101": "Auxiliar", "5103": "Auxiliar", "5120": "Auxiliar",
    "6105": "Auxiliar", "6106": "Auxiliar", "6107": "Auxiliar", "6108": "Auxiliar",
    "6109": "Auxiliar", "6111": "Auxiliar", "6112": "Auxiliar", "6113": "Auxiliar",
    "6114": "Auxiliar", "6115": "Auxiliar", "6116": "Auxiliar", "6132": "Auxiliar",
    "6133": "Auxiliar", "6134": "Auxiliar", "6135": "Auxiliar", "6136": "Auxiliar",
    "6137": "Auxiliar", "6140": "Auxiliar", "6141": "Auxiliar", "6142": "Auxiliar",
    "7106": "Auxiliar", "7107": "Auxiliar", "7108": "Auxiliar", "7109": "Auxiliar",
    "7110": "Auxiliar", "7111": "Auxiliar", "7112": "Auxiliar", "7113": "Auxiliar",
    "E8108": "Auxiliar", "E8109": "Auxiliar", "E8120": "Auxiliar",
    "R9103": "Auxiliar"
}

def obtener_alertas_desde_json(id_vehiculo, path_json="data/tag_vehicle_group_rear_change_heading.json"):
    alertas_validadas = []
    id_vehiculo = str(id_vehiculo) # Asegurar string
    
    try:
        with open(path_json, 'r', encoding='utf-8') as f:
            datos_raw = json.load(f)
            
        # Buscamos la tabla específica en la estructura del export
        #
        for item in datos_raw:
            if item.get("type") == "table" and item.get("name") == "tag_vehicle_group_rear_change_heading":
                for entrada in item["data"]:
                    # Filtramos por ID y por el Flag de giro 180
                    if entrada["id_vehicle"] == id_vehiculo and entrada["flg_change_180"] == "1":
                        alertas_validadas.append({
                            "vehiculo": entrada["id_vehicle"],
                            "datetime": entrada["datetime"], # "2026-01-22 07:17:53"
                            "lat": float(entrada["lat"]),
                            "lon": float(entrada["lon"]),
                            "validado": None
                        })
        return alertas_validadas
    except Exception as e:
        print(f"Error procesando el JSON masivo: {e}")
        return []
    
def obtener_pool_alertas(id_numerico, fecha_str, path_json, modo="operacion"):
    """
    Filtra alertas estrictamente por ID y Rango de tiempo (7am a 7am).
    """
    pool = []
    formato = "%Y-%m-%d %H:%M:%S"
    
    # Definicion del rango operativo para el dia 'f' solicitado
    if modo == "operacion":
        inicio_rango = datetime.strptime(f"{fecha_str} 07:00:00", formato)
        fin_rango = inicio_rango + timedelta(hours=24) - timedelta(seconds=1)
    else:
        inicio_rango = datetime.strptime(f"{fecha_str} 00:00:00", formato)
        fin_rango = datetime.strptime(f"{fecha_str} 23:59:59", formato)

    try:
        with open(path_json, 'r', encoding='utf-8') as f:
            datos = json.load(f)
            
        for item in datos:
            if item.get("type") == "table" and item.get("name") == "tag_vehicle_group_rear_change_heading":
                for entrada in item["data"]:
                    # Limpiamos posibles espacios en blanco en el ID y la fecha
                    id_json = str(entrada["id_vehicle"]).strip()
                    dt_alerta = datetime.strptime(entrada["datetime"].strip(), formato)
                    
                    # FILTRO ESTRICTO: ID + FLAG 180 + RANGO DE FECHA
                    if (id_json == str(id_numerico) and 
                        entrada["flg_change_180"] == "1" and 
                        inicio_rango <= dt_alerta <= fin_rango):
                        
                        pool.append({
                            "vehiculo": id_json,
                            "datetime": entrada["datetime"],
                            "lat": float(entrada["lat"]),
                            "lon": float(entrada["lon"]),
                            "speed": entrada.get("speed", "N/A")
                        })
        return pool
    except Exception as e:
        print(f"Error critico en data_handler: {e}")
        return []
    
def determinar_tipo_y_id(id_input):
    """Detecta automáticamente el tipo de vehículo y extrae el ID numérico."""
    id_clean = id_input.strip().upper()
    id_num = re.sub(r'\D', '', id_clean)
    
    # Intenta obtener del diccionario, si no, usa reglas lógicas
    categoria = CATEGORIAS_FLOTA.get(id_clean)
    if not categoria:
        if id_clean.startswith("LV") or id_clean.startswith("EQ"): categoria = "Ligero"
        elif id_clean.startswith("S"): categoria = "Pala"
        elif id_clean.startswith("HT") or id_clean.startswith("C"): categoria = "Camión"
        else: categoria = "Auxiliar"
    return id_clean, id_num, categoria


def generar_lista_fechas(inicio_str, fin_str):
    """Genera lista de strings YYYY-MM-DD entre dos fechas inclusivas."""
    inicio = datetime.strptime(inicio_str, "%Y-%m-%d")
    fin = datetime.strptime(fin_str, "%Y-%m-%d")
    lista = []
    curr = inicio
    while curr <= fin:
        lista.append(curr.strftime("%Y-%m-%d"))
        curr += timedelta(days=1)
    return lista