
from bs4 import BeautifulSoup
from datetime import datetime
from glob import glob
import pandas as pd
import json
import argparse
import sys
import re


# ../data/raw/json/pagina_1_2025_12_28-12h_33m.html
def get_date_filename(html_filename: str):
    """Genera el nombre del archivo JSONL basado en la fecha del HTML input"""
    
    # Busqueda del patron YYYY_MM_DD-HHh_MMm
    match = re.search(r'\d{4}_\d{2}_\d{2}-\d{2}h_\d{2}m', str(html_filename))
    
    if match:
        fecha = match.group()
    else:
        print(f"Advertencia: No se encontró fecha en '{html_filename}', usando fecha actual.")
        fecha = datetime.now().strftime('%Y_%m_%d-%Hh_%Mm')
    
    return fecha


def read_html(file):
    """Abre un archivo HTML y retorna un objeto de BeautifulSoup"""
    with open(file, 'r', encoding='utf-8') as f:
        html = BeautifulSoup(f, 'html.parser')
    return html


def get_cards(html):
    """Encuentra las etiquetas <a> dentro del HTML donde el attribute 'data-testid' contenga 'card-product' dentro."""
    a_tags = html.find_all('a')
    cards = []
    for a in a_tags:
        if 'data-testid' in a.attrs and 'card-product' in a['data-testid']:
            cards.append(a)
    return cards


def json_cleaner(json_raw_path, json_cleaned_path):
    df = pd.read_json(json_raw_path, lines=True)

    df['id'] = df['id'].astype(str)
    df['slug'] = df['slug'].astype(str)
    df['city'] = df['city'].astype("category")
    df['gear'] = df['gear'].astype("category")
    df['details'] = df['details'].astype("string")
    df['year'] = df['year'].astype("Int64")
    df['km'] = df['km'].astype("Int64")

    df_sorted = df.sort_values('km', na_position='last')

    df_final = df_sorted.drop_duplicates(subset=['id'], keep='first')
    df_final.to_json(json_cleaned_path, orient='records', lines=True)


def main(htmls_path):
    """Si no se le pasa un archivo json, tomara el ultimo"""
    date_filename = get_date_filename(htmls_path[0])
    json_raw_path = f"../data/raw/json/dataset_autos_{date_filename}.jsonl"

    with open(json_raw_path, 'w', encoding='utf-8') as f:
        
        for file in htmls_path:
            html = read_html(file)  
            cards = get_cards(html) 
            print(len(cards), f"tarjetas encontradas en el html: {file}")
            
            for c in cards:
                id = c['data-testid'].replace('-', ' ').split()[-1]
                slug = c['href']

                # Encontramos el precio del vehiculo en la card, si no tiene continua con la siguiente iteracion.
                span_price = c.find(class_=re.compile(".*amount__large__price.*"))
                if span_price:
                    price = int(span_price.string.replace(',', '').strip())
                else: continue
        
                # Extraccion de ciudad
                footer = c.find(class_=re.compile(".*product_cardProduct__footerInfo.*"))
                if footer:
                    try:
                        ciudad = footer.string.split('•')[0].strip()
                    except Exception as e:
                        ciudad = None

                # Extraccion del subtitulo con anio, Kilometraje, Engine y Tipo de caja 
                # "subtitulo": ["2019 ", " 71,021 km ", " 2.0 EX AUTO ", " Autom\u00e1tico"]
                subtitle = c.find(class_=re.compile(".*Product__subtitle.*"))
                if subtitle: 
                    try:
                        subtitle = subtitle.string.split('•')
                        year = int(subtitle[0].strip())
                        km_str = subtitle[1].lower().replace('km', '').replace(',', '').strip()
                        km = int(km_str)
                        details = subtitle[2].strip()
                        shift = subtitle[3].strip()
                    except (ValueError, IndexError):
                        year, km, details, shift = None, None, None, None
                else: continue
                
                # Extraccion de banners
                hot_sale_flag = 0
                banner = c.find(string=re.compile("Precio imbatible"))
                if banner:
                    hot_sale_flag = 1
                
                f.write(
                    json.dumps(
                        {"id":id, 
                         "slug":slug,
                         "city": ciudad, 
                         "price":price, 
                         "year" : year,
                         "km": km,
                         "gear": shift,
                         "discount_offer": hot_sale_flag,
                         "details": details
                         }) + '\n')
                
    json_cleaned_path = f"../data/processed/json/dataset_autos_{date_filename}.jsonl"
    json_cleaner(json_raw_path, json_cleaned_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        '--path', 
        type=str,
        required=False,
        help='Ruta de los archivos HTML'
        )
    
    args = parser.parse_args([])

    if not args.path:
        directories = glob('../data/raw/raw_html/*/', recursive=False)
        
        if not directories:
            print("No se encontraron carpetas en la ruta.")
            sys.exit()

        directories.sort()
        last_dir = directories[-1]
        
        html_filenames_path = glob(f"{last_dir}*.html")
        print(f"Utilizando ultima carpeta: '{last_dir}'")
        main(html_filenames_path)
        
    else:
        path = glob(f"{args.path}/*.html")
        main(path)


