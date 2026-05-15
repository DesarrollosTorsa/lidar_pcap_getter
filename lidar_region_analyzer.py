import pandas as pd
import matplotlib.pyplot as plt
import glob
import os

def analyze_lidar_csv(file_path):
    # 1. Extraer metadatos del nombre del archivo
    # Formato: frame_S2164_RIGHT_selected_vehicle.csv
    base_name = os.path.basename(file_path)
    name_no_ext = os.path.splitext(base_name)[0]
    parts = name_no_ext.split('_')
    
    try:
        # Asumiendo que parts[1] siempre será el ID de la Pala (S2050, S2164, etc.)
        pala_id = parts[1]    
        position = parts[2]   # RIGHT, LEFT, REAR
        obj_type = parts[-1]  # vehicle, talud, etc.
    except IndexError:
        pala_id, position, obj_type = "Unknown", "Unknown", "Unknown"

    print(f"Procesando: {base_name} [Pala: {pala_id} | Sensor: {position}]...")

    # 2. Cargar y limpiar datos
    try:
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()
    except Exception as e:
        print(f"Error al leer {base_name}: {e}")
        return

    # 3. Estadísticas clave
    stats = {
        'ID Pala': pala_id,
        'Sensor': position,
        'Objeto': obj_type.upper(),
        'Total Puntos': len(df),
        'Media Intensidad': df['intensity'].mean(),
        'P95 Intensidad': df['intensity'].quantile(0.95),
        'Distancia Mín': df['distance'].min(),
        'Distancia Med': df['distance'].mean()
    }

    # 4. Crear Visualización
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Color dinámico: Azul para vehículos, Naranja para talud/roca
    color = '#3498db' if 'vehicle' in obj_type.lower() else '#e67e22'
    
    # Histograma
    ax.hist(df['intensity'], bins=range(0, int(df['intensity'].max()) + 2), 
            color=color, edgecolor='black', alpha=0.7)

    # Título corregido para mostrar la Pala
    plt.title(f'Análisis de Reflectividad | Pala: {pala_id} | Lidar: {position}\nObjeto: {obj_type.upper()}', 
              fontsize=13, fontweight='bold')
    
    ax.set_xlabel('Valor de Intensidad (Reflectividad)', fontsize=11)
    ax.set_ylabel('N° de Puntos', fontsize=11)
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    # Cuadro de estadísticas
    text_str = '\n'.join([f"{k}: {v:.2f}" if isinstance(v, float) else f"{k}: {v}" for k, v in stats.items()])
    props = dict(boxstyle='round', facecolor='white', alpha=0.8)
    ax.text(0.65, 0.95, text_str, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', bbox=props, family='monospace')

    # 5. Guardar imagen
    output_name = f"reporte_{name_no_ext}.png"
    plt.tight_layout()
    plt.savefig(output_name, dpi=300)
    plt.close()
    print(f"  --> Generado: {output_name}\n")

if __name__ == "__main__":
    files = glob.glob("frame_*.csv")
    
    if not files:
        print("No se encontraron archivos 'frame_*.csv'.")
    else:
        print(f"Analizando {len(files)} muestras de palas...\n")
        for f in files:
            analyze_lidar_csv(f)
        print("Proceso completado.")