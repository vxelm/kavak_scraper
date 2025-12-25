from glob import glob
from bs4 import BeautifulSoup
import json
import re

html_filenames = glob('../data/raw_html/*.html')


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


def main():
    with open('../data/dataset_autos.jsonl', 'w', encoding='utf-8') as f:
        
        for file in html_filenames:
            html = read_html(file)  
            cards = get_cards(html) 
            print(len(cards), f"tarjetas encontradas en el html: {file}")
            
            for c in cards:
                id = c['data-testid'].replace('-', ' ').split()[-1]
                slug = c['href']

                # Encontramos el precio del vehiculo en la card, si no tiene continua con la siguiente iteracion.
                span_price = c.find(class_=re.compile(".*amount__large__price.*"))
                if span_price:
                    price = span_price.string.replace(',', '')
                else: continue
        
                f.write(json.dumps({"id":id, "slug":slug, "price":price}) + '\n')


if __name__ == '__main__':
    main()


