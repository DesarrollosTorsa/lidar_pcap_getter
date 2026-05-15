@echo off
title LiDAR PCAP Getter - Antapaccay
echo.
echo  ==========================================
echo   LiDAR PCAP Getter - Antapaccay
echo  ==========================================
echo.

:: Verificar que existe el entorno virtual
if not exist "venv\Scripts\activate.bat" (
    echo  [ERROR] Entorno virtual no encontrado.
    echo.
    echo  Ejecuta esto una sola vez para instalarlo:
    echo    python -m venv venv
    echo    venv\Scripts\activate
    echo    pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

:: Verificar que existe el .env
if not exist "config\.env" (
    echo  [ERROR] No se encontro config\.env
    echo.
    echo  Copia el archivo de ejemplo y completa las credenciales:
    echo    copy config\.env.example config\.env
    echo.
    pause
    exit /b 1
)

call venv\Scripts\activate

:: Si se pasaron argumentos, ejecutar directamente
if not "%1"=="" (
    python main.py %*
    goto fin
)

:: Modo interactivo para no-devs
echo  Modo interactivo
echo  ----------------------------------------
set /p DURACION="  Duracion de captura en ms (ej. 15000 = 15s): "
echo.
echo  Formato de equipos: S2160:RIGHT  o  S2051:LEFT,REAR,RIGHT
echo  Separar varios equipos con espacios: S2160:RIGHT S2051:LEFT,REAR
echo.
set /p TARGETS="  Equipos y posiciones: "
echo.

python main.py %DURACION% %TARGETS%

:fin
echo.
pause
