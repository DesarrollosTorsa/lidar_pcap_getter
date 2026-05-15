# lidar_pcap_getter

Herramienta CLI para capturar y descargar datos LiDAR (.pcap comprimidos en .zip) desde palas y equipos mineros en Antapaccay. Automatiza la cadena completa: conexión SSH en tres saltos, disparo del comando de captura, verificación del archivo generado y descarga al equipo local.

---

## Arquitectura de conexión

```
Laptop (WSL) ──SSH──► Servidor Antapaccay ──SSH tunnel──► Concentrador CM (Raspberry Pi)
                                                                    │
                                                          Ejecuta nc 127.0.0.1:12001
                                                          Genera /tmp/LidarDataRaw/<nombre>.zip
```

El puerto del concentrador se calcula automáticamente según el ID del equipo:

| Tipo | Regla | Ejemplo |
|---|---|---|
| Ligero con ID de 3 dígitos | `12000 + ID` | LV181 → puerto 12181 |
| Todos los demás | `ID` directamente | S2160 → puerto 2160 |

---

## Requisitos

- Python 3.10+
- Acceso SSH al servidor Antapaccay (credenciales en `config/.env`)
- Los equipos deben estar encendidos y con el servicio LiDAR activo

### Dependencias Python

```bash
pip install paramiko python-dotenv
```

O con el entorno virtual incluido:

```bash
python -m venv venv
source venv/bin/activate
pip install paramiko python-dotenv
```

---

## Instalación

```bash
git clone git@github.com:DesarrollosTorsa/lidar_pcap_getter.git
cd lidar_pcap_getter

python -m venv venv
source venv/bin/activate
pip install paramiko python-dotenv
```

Copiar y rellenar el archivo de configuración:

```bash
cp config/.env.example config/.env
```

Editar `config/.env` con las credenciales reales:

```env
SRV_HOST="X.X.X.X"
SRV_PORT=33322
SRV_USER="usuario"
SRV_PASS="contraseña"

EQUIP_USER="pi"
EQUIP_PASS="contraseña_equipos"

PANTALLA_IP="192.168.19.100"

# Opcional: ruta a Descargas de Windows (solo en WSL)
WIN_DOWNLOADS="/mnt/c/Users/TU_USUARIO/Downloads"
```

---

## Estructura del proyecto

```
lidar_pcap_getter/
├── main.py                  # Script principal de orquestación
├── lidar_region_analyzer.py # Análisis de regiones LiDAR desde CSV
├── conexion/
│   └── ssh_manager.py       # Gestión de saltos SSH con paramiko
├── utils/
│   ├── env_handler.py       # Carga de credenciales desde .env
│   ├── logger.py            # Logger unificado
│   └── data_handler.py      # Utilidades de flota y fechas
├── data/
│   └── fleet_info.json      # Mapeo de IDs de equipos (S2160 → Pala, LV181 → Ligero…)
├── config/
│   ├── .env.example         # Plantilla de configuración
│   └── param_mapping.json   # Mapeo de parámetros técnicos
└── descargas/               # Zips descargados (generado automáticamente, no versionado)
    └── YYYYMMDD/            # Subcarpeta por fecha de sesión
```

---

## Uso

### Captura única

```bash
python main.py <duration_ms> <EQUIPO:POSICION>
```

```bash
python main.py 15000 S2160:RIGHT
```

### Batch — varios equipos y posiciones en un solo comando

```bash
python main.py 15000 S2051:LEFT,REAR,RIGHT S2160:REAR,RIGHT S2162:LEFT,RIGHT
```

### Batch — desde archivo JSON

```bash
python main.py 15000 --batch captures.json
```

Formato `captures.json`:

```json
[
  {"equipo": "S2051", "positions": ["LEFT", "REAR", "RIGHT"]},
  {"equipo": "S2160", "positions": ["REAR", "RIGHT"]}
]
```

### Opciones adicionales

| Flag | Descripción |
|---|---|
| `--override` | Sobreescribe archivos existentes sin preguntar |
| `--solo-captura` | Dispara la captura pero no descarga el zip |

### Comportamiento cuando el archivo ya existe

Si el archivo ya existe en el concentrador, el script pregunta:

```
  [!] Ya existe: 2160_RIGHT_20260408.zip
      -rw-r--r-- 1 root root 8367430 abr 8 09:05 /tmp/LidarDataRaw/2160_RIGHT_20260408.zip
      Opciones: [s] Re-capturar y sobreescribir  [d] Descargar el existente  [N] Saltar
      ¿Qué hacer? [s/d/N]:
```

---

## Nomenclatura de archivos

```
<ID_NUMERICO>_<POSICION>_<YYYYMMDD>.zip

Ejemplos:
  2160_RIGHT_20260408.zip
  2051_LEFT_20260408.zip
```

Posiciones válidas: `LEFT`, `RIGHT`, `REAR`

---

## Destino de las descargas

Los archivos se guardan en dos lugares:

1. **Local WSL:** `./descargas/YYYYMMDD/<nombre>.zip`
2. **Windows** *(si `WIN_DOWNLOADS` está configurado en `.env`)*: `C:\Users\...\Downloads\YYYYMMDD\<nombre>.zip`

La subcarpeta con la fecha se crea automáticamente al iniciar cada sesión.

---

## Casos de uso

**Captura de diagnóstico rápida (15 s) de una pala:**
```bash
python main.py 15000 S2163:RIGHT
```

**Sesión completa de una pala (todos los sensores, 1 minuto cada uno):**
```bash
python main.py 60000 S2160:LEFT,REAR,RIGHT
```

**Ronda de mantenimiento — múltiples palas:**
```bash
python main.py 30000 S2050:LEFT,RIGHT S2051:LEFT,REAR,RIGHT S2160:RIGHT S2170:LEFT,REAR,RIGHT
```

**Descargar un zip ya generado sin re-capturar:**
```bash
python main.py 15000 S2161:RIGHT
# → responder "d" al prompt
```

---

## Equipos soportados

El archivo `data/fleet_info.json` contiene el mapeo completo de la flota:

| Categoría | Prefijos | Ejemplo |
|---|---|---|
| Palas | S | S2160, S2051 |
| Camiones | HT, C | HT3073, C1060 |
| Ligeros | LV, EQ | LV181, EQ1164 |
| Auxiliares | numéricos, E, R | 6105, E8108 |
