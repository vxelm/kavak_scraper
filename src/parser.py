import logging
import sys
import re
from glob import glob

from typing import List, Dict, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from pydantic import ValidationError
from bs4.element import Tag

from src.logger import setup_logging
from src.schemas import Autokavak
from src import settings


#Patterns 
SPAN_PRICE_PATTERN = re.compile(".*amount__large__price.*")
FOOTER_PATTERN = re.compile(".*product_cardProduct__footerInfo.*")
SUBTITLE_PATTERN = re.compile(".*Product__subtitle.*")
HOT_SALE_PATTERN = re.compile("Precio imbatible")
RESERVED_PATTERN = re.compile("Apartado")

logger = logging.getLogger(__name__)


def get_date_filename(html_filename: str) -> str:
    """Genera el nombre del archivo JSONL basado en la fecha del HTML input"""
    
    # Busqueda del patron YYYY_MM_DD-HHh_MMm
    match = re.search(r'\d{4}_\d{2}_\d{2}-\d{2}h_\d{2}m', str(html_filename))
    
    if match:
        fecha = match.group()
    else:
        logger.warning("Advertencia: No se encontró fecha en '%s', usando fecha actual.", html_filename)
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
    """Encontramos el precio del vehiculo en la card, si no tiene continua con la siguiente iteracion."""
    price_span = card.find(class_=SPAN_PRICE_PATTERN)
    if price_span:
        try:
            price_text = price_span.get_text(strip=True).replace(',', '').replace('$', '')
            price = int(price_text)
            return price
        except (ValueError, AttributeError) as e:
            logger.warning("El auto con id: %s no tiene precio. Error: %s", car_id, e)
    return None


def extract_city(card: Tag, car_id: str) -> Optional[str]:
    city_tag = card.find(class_=FOOTER_PATTERN)
    if city_tag:
        try:
            raw_text = city_tag.get_text(strip=True)
            ciudad = raw_text.split('•')[0].strip()
            return ciudad

        except AttributeError as e:
            logger.warning("El auto con id: %s no tiene ciudad. Error: %s", car_id, e)
    return None


def extract_subtitle(card: Tag, car_id: str) -> Dict:
    """Extraccion del subtitulo con anio, Kilometraje, Engine y Tipo de caja """
    # "subtitulo": ["2019 ", " 71,021 km ", " 2.0 EX AUTO ", " Autom\u00e1tico"]
    subtitle_elements = {"year": None, "km": None, "details": None, "shift": None}
    subtitle_tag = card.find(class_=SUBTITLE_PATTERN)
    if subtitle_tag: 
        try:
            subtitle_parts = [part.strip() for part in subtitle_tag.get_text(strip=True).split('•')]

            subtitle_elements["year"] = int(subtitle_parts[0])
            subtitle_elements["km"] = int(subtitle_parts[1].lower().replace('km', '').replace(',', '').strip())
            subtitle_elements["details"] = subtitle_parts[2].strip()

            if len(subtitle_parts) > 3:
                subtitle_elements["shift"] = subtitle_parts[3].strip()
            
        except (ValueError, IndexError, AttributeError) as e:
            logger.warning("El auto ID: %s no tiene un dato. Error: %s", car_id, e)

    return subtitle_elements


def extract_banner(card: Tag, pattern: re.Pattern[str]) -> bool:
    """Extraccion de banners"""
    banner = False
    banner_tag = card.find(string=pattern)
    if banner_tag:
        banner = True
    return banner


def main(htmls_path: List[str]) -> None:
    # Configurando logger
    setup_logging()
    
    # Si no se le pasa un archivo json, tomara el ultimo
    date_filename = get_date_filename(htmls_path[0])
    filename = date_filename + ".jsonl"
    json_raw_path = settings.RAW_JSON_DIR / filename

    with open(json_raw_path, 'w', encoding='utf-8') as f:
        id_set_autos = set()
        
        for file in htmls_path:
            html = read_html(file)  
            cards = get_cards(html) 
            logger.info("%s tarjetas encontradas en el html: %s", len(cards), file)
            
            for c in cards:
                car_id = c['data-testid'].replace('-', ' ').split()[-1]
                
                if car_id in id_set_autos:
                    continue    

                id_set_autos.add(car_id)

                slug = c['href']
                price = extract_price(c, car_id)
                city = extract_city(c, car_id)
                subtitle = extract_subtitle(c, car_id)
                hot_sale_flag = extract_banner(c, HOT_SALE_PATTERN)
                is_reserved = extract_banner(c, RESERVED_PATTERN)

                try:
                    auto_valido = Autokavak(
                        id=car_id,
                        slug=slug,
                        city=city,
                        price=price,
                        year=subtitle.get('year'),
                        km=subtitle.get('km'),
                        gear=subtitle.get('shift'),
                        discount_offer=hot_sale_flag,
                        is_reserved=is_reserved,
                        details=subtitle.get('details')
                    )

                    f.write(
                        auto_valido.model_dump_json() + '\n'
                    )
                    if len(id_set_autos) % 100 == 0:
                        f.flush()

                except ValidationError as e:
                    logger.error("Datos corruptos en auto %s en %s. Error: %s", car_id, file, e.errors())



if __name__ == '__main__':
    directories = glob(f'{settings.RAW_HTML_DIR}/*/', recursive=False)
    
    if not directories:
        logger.warning("No se encontraron carpetas en la ruta.")
        sys.exit()

    directories.sort()
    last_dir = directories[-1]
    
    html_filenames_path = glob(f"{last_dir}*.html")
    logger.info("Utilizando ultima carpeta: %s", last_dir)
    main(html_filenames_path)