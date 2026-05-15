@echo off
title Construyendo LiDAR PCAP Getter...
echo.
echo  Construyendo ejecutable para Windows...
echo  ========================================
echo.

:: Activar entorno virtual
if not exist "venv\Scripts\activate.bat" (
    echo  [ERROR] Entorno virtual no encontrado. Ejecuta primero:
    echo    python -m venv venv ^& venv\Scripts\activate ^& pip install -r requirements.txt
    pause
    exit /b 1
)
call venv\Scripts\activate

:: Instalar PyInstaller si no está
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo  Instalando PyInstaller...
    pip install pyinstaller
)

:: Limpiar builds anteriores
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

:: Construir
echo  Empaquetando...
pyinstaller lidar_pcap_getter.spec

if errorlevel 1 (
    echo.
    echo  [ERROR] Fallo el build. Revisa los mensajes de arriba.
    pause
    exit /b 1
)

echo.
echo  ========================================
echo   Build exitoso!
echo  ========================================
echo.
echo  Ejecutable: dist\lidar_pcap_getter.exe
echo.
echo  Para distribuirlo, copia estos archivos juntos:
echo    - dist\lidar_pcap_getter.exe
echo    - config\.env.example  (renombrar a config\.env y completar)
echo.
pause
