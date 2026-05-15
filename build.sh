#!/bin/bash
echo ""
echo " Construyendo ejecutable para Linux..."
echo " ========================================"
echo ""

source venv/bin/activate

# Instalar PyInstaller si no está
if ! pip show pyinstaller &>/dev/null; then
    echo " Instalando PyInstaller..."
    pip install pyinstaller
fi

# Limpiar builds anteriores
rm -rf dist build

echo " Empaquetando..."
pyinstaller lidar_pcap_getter.spec

if [ $? -ne 0 ]; then
    echo ""
    echo " [ERROR] Fallo el build."
    exit 1
fi

echo ""
echo " ========================================"
echo "  Build exitoso!"
echo " ========================================"
echo ""
echo " Ejecutable: dist/lidar_pcap_getter"
echo ""
echo " Para distribuirlo, copia estos archivos juntos:"
echo "   - dist/lidar_pcap_getter"
echo "   - config/.env.example  (renombrar a config/.env y completar)"
echo ""
