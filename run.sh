#!/bin/bash
echo ""
echo " =========================================="
echo "  LiDAR PCAP Getter - Antapaccay"
echo " =========================================="
echo ""

# Verificar entorno virtual
if [ ! -f "venv/bin/activate" ]; then
    echo " [ERROR] Entorno virtual no encontrado."
    echo ""
    echo " Ejecuta esto una sola vez para instalarlo:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    echo ""
    exit 1
fi

# Verificar .env
if [ ! -f "config/.env" ]; then
    echo " [ERROR] No se encontro config/.env"
    echo ""
    echo " Copia el archivo de ejemplo y completa las credenciales:"
    echo "   cp config/.env.example config/.env"
    echo ""
    exit 1
fi

source venv/bin/activate

# Si se pasaron argumentos, ejecutar directamente
if [ $# -gt 0 ]; then
    python main.py "$@"
    exit $?
fi

# Modo interactivo
echo " Modo interactivo"
echo " ------------------------------------------"
read -p "  Duracion de captura en ms (ej. 15000 = 15s): " DURACION
echo ""
echo "  Formato: S2160:RIGHT  o  S2051:LEFT,REAR,RIGHT"
echo "  Separar varios equipos con espacios"
echo ""
read -p "  Equipos y posiciones: " TARGETS
echo ""

python main.py $DURACION $TARGETS
