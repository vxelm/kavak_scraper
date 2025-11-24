import pandas as pd
import json
import os
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert

# CONFIGURACIÓN
# user:password@host:port/dbname
# Nota: Si corres esto desde WSL/Windows (fuera de la red Docker), el host es 'localhost'.
# Si lo corres DESDE otro contenedor, el host es 'warehouse'.
DB_URL = "postgresql://admin_data:root_password_seguro@localhost:5432/kavak_db"
INPUT_FILE = "data/raw/kavak_raw_data.jsonl" # Ajusta la ruta según desde donde ejecutes

def get_db_connection():
    return create_engine(DB_URL)

def process_and_load():
    print("🚀 Iniciando carga a PostgreSQL...")
    
    # 1. LEER JSONL (Igual que antes)
    data = []
    if not os.path.exists(INPUT_FILE):
        print(f"❌ No encuentro {INPUT_FILE}")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data.append(json.loads(line))
            except:
                continue
    
    # 2. TRANSFORMAR A DATAFRAME (Igual que antes)
    processed_data = []
    for entry in data:
        try:
            raw = entry['raw_data']
            car = next((item for item in raw.get('@graph', []) if item.get('@type') == 'Car'), None)
            
            if car:
                # Extraemos el ID del final de la URL si no viene explícito
                # Ejemplo URL: .../kia-forte-2017 -> id: kia-forte-2017
                internal_id = entry['source_url'].split('/')[-1]
                
                processed_data.append({
                    'id_interno': internal_id,
                    'url': entry['source_url'],
                    'marca': car.get('brand', {}).get('name', 'Desconocido'),
                    'modelo': car.get('model', 'Desconocido'),
                    'version': car.get('vehicleConfiguration', 'N/A'),
                    'anio': int(car.get('vehicleModelDate', 0) or 0),
                    'precio_mxn': int(car.get('offers', {}).get('price', 0) or 0),
                    'km': int(car.get('mileageFromOdometer', {}).get('value', 0) or 0),
                    'transmision': car.get('vehicleTransmission', 'N/A'),
                    'ciudad': 'Mexico',
                    'fecha_extraccion': pd.to_datetime(entry['extracted_at'], unit='s').date()
                })
        except Exception:
            continue

    df = pd.DataFrame(processed_data)
    # Deduplicación en Pandas antes de intentar subir (Optimización)
    # Nos quedamos con el ÚLTIMO registro encontrado para cada ID (el más reciente)
    df = df.drop_duplicates(subset=['id_interno'], keep='last')
    
    print(f"   📉 Registros únicos a insertar: {len(df)}")

    # 3. CARGAR (Upsert - Insert or Update)
    # Pandas to_sql es limitado para Upserts, así que usamos un truco simple:
    # 'append' fallará si hay duplicados. 
    # Para hacerlo profesional, usamos to_sql pero manejando errores o usando sqlalchemy core.
    # POR AHORA: Usaremos 'append' pero como ya limpiamos duplicados en el paso anterior (drop_duplicates),
    # y la tabla está vacía o limpia, funcionará.
    
    engine = get_db_connection()
    
    try:
        # method='multi' acelera la carga
        df.to_sql('autos_silver', engine, if_exists='append', index=False, method='multi', chunksize=1000)
        print("   ✅ Carga completada en Postgres.")
    except Exception as e:
        print(f"   ⚠️ Error en carga (probablemente IDs repetidos en DB): {e}")
        print("   💡 Tip: En producción usaríamos INSERT ON CONFLICT DO UPDATE.")

if __name__ == "__main__":
    process_and_load()