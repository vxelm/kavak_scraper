import pandas as pd
import json
import sqlite3
from datetime import datetime

# CONFIGURACIÓN
INPUT_FILE = '../data/raw/kavak_raw_data.jsonl'
DB_NAME = '../data/processed/kavak_market_v3.db'

data = []

with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data.append(json.loads(line))
        except:
            continue
    print(f"📥 Registros crudos leídos: {len(data)}")


# Tracción: Viene como URL "https://schema.org/FrontWheelDriveConfiguration"
# Tomamos lo que está después de la última barra y quitamos "Configuration"
def get_traccion(car):
    raw_drive = car.get('driveWheelConfiguration', 'Desconocido')
    traccion = raw_drive.split('/')[-1].replace('Configuration', '') if raw_drive else 'Desconocido'
    return traccion


def get_vin(car):
    vin = car.get('vehicleIdentificationNumber')
    return vin or None


# Motor: A veces es un objeto, a veces texto. Aseguramos que sea dict.
def get_engine_name(car):
    return car.get('vehicleEngine', {})  


# --- PROCESAR IMAGENES (Tabla Hija) ---
def extraer_images(car, vin):
    images_list = []
    # Recorremos todas las imágenes del auto
    lista_imgs = car.get('image', [])
    if isinstance(lista_imgs, list):
        for img_url in lista_imgs:
            images_list.append({
                'auto_id': vin, # Clave foránea al auto necesaria para conectar tablas
                'url_imagen': img_url
            })
    return images_list  


def get_data(car, entry, vin, engine_data, traccion):
    return {
                    'vin': vin,
                    'url': entry['source_url'],
                    'marca': car.get('brand', {}).get('name', 'Desconocido'),
                    'modelo': car.get('model', 'Desconocido'),
                    'version': car.get('vehicleConfiguration', 'N/A'),
                    'anio': int(car.get('vehicleModelDate', 0) or 0),
                    'precio_mxn': int(car.get('offers', {}).get('price', 0) or 0),
                    'km': int(car.get('mileageFromOdometer', {}).get('value', 0) or 0),
                    'transmision': car.get('vehicleTransmission', 'N/A'),
                    'ciudad': 'Mexico',
                    'fecha_extraccion': pd.to_datetime(entry['extracted_at'], unit='s').date(),
                    
                    # --- NUEVOS CAMPOS ---
                    'color': car.get('color', 'Desconocido'),
                    'tipo_cuerpo': car.get('bodyType', 'Desconocido'), # Ej: SUV
                    'combustible': engine_data.get('fuelType', 'N/A'), # Ej: Gasolina
                    'motor': engine_data.get('name', 'N/A'),           # Ej: Motor 2.0 SEL
                    'traccion': traccion,                              # Ej: FrontWheelDrive
                }


images_list = []
processed_data = []

for entry in data:
    try:
        raw = entry['raw_data']
        car = next((item for item in raw.get('@graph',[]) if item.get('@type') == 'Car'), None)
        
        if car:
                vin = get_vin(car)
                if not vin:
                     print(f"⚠️ Auto sin VIN, se omite: {entry['source_url']}")
                     continue

                traccion = get_traccion(car)
                images_list.append(extraer_images(car, vin))
                engine_data = get_engine_name(car)
                processed_data.append(get_data(car, entry, vin, engine_data, traccion))
                
    except Exception as e:
        continue


df = pd.DataFrame(processed_data)
df = df.drop_duplicates(subset=['id_interno'])
print(f"📊 Registros procesados: {len(df)}")


df_images = pd.DataFrame([img for sublist in images_list for img in sublist])
df_images = df_images.drop_duplicates(subset=['url_imagen'])
print(f"📸 Imágenes procesadas: {len(df_images)}")


# --- LIMPIEZA DE TIPOS (TYPE CASTING) ---
df['anio'] = pd.to_numeric(df['anio'], errors='coerce').fillna(0).astype(int)
df['km'] = pd.to_numeric(df['km'], errors='coerce').fillna(0).astype(int)
df['precio_mxn'] = pd.to_numeric(df['precio_mxn'], errors='coerce').fillna(0).astype(int)

print(f"   ✨ Registros limpios listos para SQL: {len(df)}")
print(df.dtypes) 


# 3. CARGAR (Load to SQL)
conn = sqlite3.connect(DB_NAME)

df.to_sql('autos', conn, if_exists='replace', index=False)

conn.close()
print(f"💾 Datos guardados exitosamente en {DB_NAME}")


