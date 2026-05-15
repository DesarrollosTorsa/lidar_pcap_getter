Markdown
# Protocolo de Captura LiDAR - Proyecto lidar_pcap_getter

Este documento define las reglas para que Claude opere el sistema de captura de paquetes (.pcap) desde los LiDARs de las palas.

## 1. Arquitectura de Conexión (El Salto Triple)
Para llegar a la pantalla donde se ejecuta el comando `nc`, se sigue esta cadena:
1. **Laptop (Local):** WSL Ubuntu (torsa@LAPTOP-8B2KI882).
2. **Servidor Principal (Antapaccay):** IP `SRV_HOST`, puerto `SRV_PORT`.
3. **Concentrador (CM Raspberry):** Se accede desde el servidor vía `ssh pi@localhost -p [PORT_ASIGNADO]`.
4. **Pantalla (CM Raspberry):** Se accede desde el concentrador a la IP `192.168.19.100` (`PANTALLA_IP`).

## 2. Reglas de Nombrado y Comandos
Los archivos de captura deben seguir estrictamente este formato:
- **Formato:** `[PALA_ID]_[POSITION]_[YYYYMMDD]`
- **Ejemplo:** `2160_RIGHT_20260406`

### Comando de Captura (Ejecutar en la Pantalla):
```bash
echo "SAVE_LIDAR_DATA_RAW=ENABLE:TRUE,NAME:[NOMBRE],SPLIT_PATHS:FALSE,ALL_DATA:TRUE,POSITION:[POS],ZIP_DATA:TRUE,TIME_SAVE:[MS],TCP_DUMP_SAVE:TRUE;" | nc -N 127.0.0.1 12001
Nota: El flag -N en nc es obligatorio para cerrar el socket tras enviar el mensaje.

3. Estructura de Archivos del Proyecto
data/fleet_info.json: Mapeo de IDs de palas (ej. S2050 -> 2050).

conexion/ssh_manager.py: Clase para gestionar los saltos SSH.

utils/env_handler.py: Carga las credenciales del .env.

config/.env: Contiene SRV_USER, SRV_PASS, EQUIP_PASS, etc.

4. Flujo de Trabajo para Claude Code
Cuando se solicite una captura o descarga:

Mapeo: Consultar data/fleet_info.json para obtener el ID numérico de la pala.

Generación de Comando: Construir el string de nc con la posición (LEFT, REAR, RIGHT) y el tiempo en ms.

Ejecución Remota: - Usar ssh_manager.py para orquestar los saltos.

El comando se debe ejecutar en el entorno de la Pantalla.

Recuperación (Download):

El archivo resultante estará en /tmp/[NOMBRE].zip dentro de la Pantalla.

Realizar el camino inverso para traer el archivo a la laptop local:
Pantalla -> Concentrador -> Servidor -> Laptop

Guardar en el directorio local ./descargas/ (crearlo si no existe o mejor teniendo en cuenta que estamos en:  torsa@LAPTOP-8B2KI882:~/proyectos/lidar_pcap_getter$ ).

5. Scripts de Referencia
Para logs, usar utils/logger.py.

Para procesar datos de la flota, usar utils/data_handler.py.