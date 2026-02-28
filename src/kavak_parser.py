
from bs4 import BeautifulSoup
from datetime import datetime
from Logger import setup_logging
from glob import glob
from typing import List, Dict, Optional
from bs4.element import Tag
import logging
import settings
import pandas as pd
import json
import argparse
import sys
import re


#Patterns 
SPAN_PRICE_PATTERN = re.compile(".*amount__large__price.*")
FOOTER_PATTERN = re.compile(".*product_cardProduct__footerInfo.*")
SUBTITLE_PATTERN = re.compile(".*Product__subtitle.*")
BANNER_PATTERN = re.compile("Precio imbatible")


setup_logging("logs_2026_02_28-14h_44m")
logger = logging.getLogger(__name__)


def get_date_filename(html_filename: str) -> str:
    """Genera el nombre del archivo JSONL basado en la fecha del HTML input"""
    
    # Busqueda del patron YYYY_MM_DD-HHh_MMm
    match = re.search(r'\d{4}_\d{2}_\d{2}-\d{2}h_\d{2}m', str(html_filename))
    
    if match:
        fecha = match.group()
    else:
        print(f"Advertencia: No se encontró fecha en '{html_filename}', usando fecha actual.")
        fecha = datetime.now().strftime('%Y_%m_%d-%Hh_%Mm')
    
    return fecha


def read_html(file: str) -> BeautifulSoup:
    """Abre un archivo HTML y retorna un objeto de BeautifulSoup"""
    with open(file, 'r', encoding='utf-8') as f:
        html = BeautifulSoup(f, 'html.parser')
    return html


def get_cards(html: BeautifulSoup) -> List[Tag]:
    """Encuentra las etiquetas <a> dentro del HTML donde el attribute 'data-testid' contenga 'card-product' dentro."""
    return [
        tag for tag in html.find_all('a')
        if tag.get('data-testid') and 'card-product' in tag.get('data-testid')
    ]


def extract_price(card: Tag, car_id: str) -> Optional[int]:
    # Encontramos el precio del vehiculo en la card, si no tiene continua con la siguiente iteracion.
    price_span = card.find(class_=SPAN_PRICE_PATTERN)
    if price_span:
        try:
            price = int(price_span.get_text(strip=True).replace(',', ''))
            return price
        except (ValueError, AttributeError) as e:
            logger.warning("El auto con id: %s no tiene precio. Error: %s", car_id, e)
    return None


def extract_city(card: Tag, car_id: str) -> Optional[str]:
    # Extraccion de ciudad
    city_tag = card.find(class_=FOOTER_PATTERN)
    if city_tag:
        try:
            raw_text = city_tag.get_text(strip=True)
            ciudad = raw_text.split('•')[0].strip()
            return ciudad

        except AttributeError as e:
            logger.warning("El auto con id: %s no tiene ciudad. Error: %s", car_id, e)
    return None


def extract_subtitle(card: Tag, car_id: str) -> Optional[Dict]:
    # Extraccion del subtitulo con anio, Kilometraje, Engine y Tipo de caja 
    # "subtitulo": ["2019 ", " 71,021 km ", " 2.0 EX AUTO ", " Autom\u00e1tico"]
    subtitle_tag = card.find(class_=SUBTITLE_PATTERN)
    if subtitle_tag: 
        try:
            subtitle = subtitle_tag.get_text(strip=True)
            year = int(subtitle[0].strip())
            km = int(subtitle[1].lower().replace('km', '').replace(',', '').strip())
            details = subtitle[2].strip()
            shift = subtitle[3].strip()
            
        except (ValueError, IndexError, AttributeError) as e:
            logger.warning("El auto ID: %s no tiene un dato. Error: %s", car_id, e)
            return None
            
        subtitle_elements = dict(
                subtitle=subtitle,
                year=year,
                km=km,
                details=details,
                shift=shift
            )
        return subtitle_elements
    return None


def extract_banner(card: Tag) -> int:
    # Extraccion de banners
    hot_sale_flag = 0
    banner = card.find(string=BANNER_PATTERN)
    if banner:
        hot_sale_flag = 1
    return hot_sale_flag


def main(htmls_path):
    """Si no se le pasa un archivo json, tomara el ultimo"""
    date_filename = get_date_filename(htmls_path[0])
    filename = date_filename + ".jsonl"
    json_raw_path = settings.RAW_JSON_DIR / filename

    with open(json_raw_path, 'w', encoding='utf-8') as f:
        id_set_autos = set()
        
        for file in htmls_path:
            html = read_html(file)  
            cards = get_cards(html) 
            print(len(cards), f"tarjetas encontradas en el html: {file}")
            
            for c in cards:
                car_id = c['data-testid'].replace('-', ' ').split()[-1]
                
                if car_id not in id_set_autos:
                    id_set_autos.add(car_id)

                    slug = c['href']
                    price = extract_price(c, car_id)
                    city = extract_city(c, car_id)
                    subtitle = extract_subtitle(c, car_id)
                    hot_sale_flag = extract_banner(c)
                    
                    if subtitle:
                        f.write(
                            json.dumps(
                                {"id":car_id, 
                                "slug":slug,
                                "city": city, 
                                "price":price, 
                                "year" : subtitle['year'],
                                "km": subtitle['km'],
                                "gear": subtitle['shift'],
                                "discount_offer": hot_sale_flag,
                                "details": subtitle['details']
                                }) + '\n')
                else:
                    logger.info("ID %s ya escaneado", car_id)
                    continue


if __name__ == '__main__':
    directories = glob(f'{settings.RAW_HTML_DIR}/*/', recursive=False)
    
    if not directories:
        print("No se encontraron carpetas en la ruta.")
        sys.exit()

    directories.sort()
    last_dir = directories[-1]
    
    html_filenames_path = glob(f"{last_dir}*.html")
    print(f"Utilizando ultima carpeta: '{last_dir}'")
    main(html_filenames_path)


