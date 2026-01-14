
from glob import glob
import sys
import pandas as pd
import json


def get_car_data(id_car, df):
    return df[df['ID_Auto'] == id_car]

def get_last_file(path: str, ext: str):
    filenames = glob(f"{path}/*{ext}")
    filenames.sort()
    return filenames[-1]


def financial_data_calculation(df_financial):
    # Calculo de datos financieros
    df_financial['Total_a_Pagar'] = (df_financial['Mensualidad'] * df_financial['Plazo']) + df_financial['Enganche_Simulado'] # Plazo * Mensualidad + enganche 

    df_financial['Interes'] = df_financial['Total_a_Pagar'] - df_financial['Precio'] # Costo extra
    df_financial['Interes_%'] = (df_financial['Interes'] * 100) / df_financial['Precio'] # % de costo extra respecto al precio  

    df_financial['Enganche_Min_%'] = (df_financial['Enganche_Min'] * 100) / df_financial['Precio']
    df_financial['Enganche_Max_%'] = (df_financial['Enganche_Max'] * 100) / df_financial['Precio']

    return df_financial


def data_merge(df_fin, df_kavak_cards):
    ### Integracion de datos faltantes (km, sucursal, caja, oferta)

    df_kavak_cards['Name'] = df_kavak_cards['slug'].str.split('/').str[-1].str.replace('_', ' ')
    df_kavak_cards[['Brand', 'Model', 'Version', 'Type', 'Year_slug']] = df_kavak_cards['Name'].str.split('-', expand=True, n=4)

    df_kavak_cards['id'] = df_kavak_cards['id'].astype('string')
    df_kavak_cards = df_kavak_cards.drop(columns=['slug', 'price', 'details']) # Elimina cols innecesarias

    cols_names = {'id':'ID_Auto', 
                'year':'Año', 
                'city':'Ciudad', 
                'gear':'Caja', 
                'km':'Km', 
                'discount_offer':'Oferta',
                'Brand': 'Marca',
                'Model': 'Modelo',
                'Type': 'Tipo'}

    df_kavak_cards.rename(columns=cols_names, inplace=True)

    df_merged = df_fin.merge(
        df_kavak_cards, 
        how='left', 
        on='ID_Auto', 
        suffixes=('_fin', '_cards')
        )
    
    df_merged['Year_slug'] = pd.to_numeric(df_merged['Year_slug'], errors='coerce')
    df_merged['Año'] = df_merged['Año'].fillna(df_merged['Year_slug'])
    df_merged = df_merged.drop(columns=['Year_slug', 'Name'])

    return df_merged


def main():
    try:    
        financial_csv_path = get_last_file('../data/processed/csv/financial_data/', '.csv')
        kavak_cards_json_path = get_last_file('../data/processed/json/', '.jsonl')

        print(financial_csv_path)
        print(kavak_cards_json_path)

    except Exception as e:
        print(f"Erro: {e}")
        sys.exit(1)
    
    dtypes = {
        #ID_Auto,Precio,Tasa_Servicio,Plazo,Mensualidad,Tasa_Interes,Seguro,Enganche_Simulado,Enganche_Min,Enganche_Max
        'ID_Auto': 'string',
        'Precio': 'float32', 
        'Tasa_Servicio': 'float32', 
        'Plazo': 'Int16',         
        'Mensualidad': 'Int32',   
        'Tasa_Interes': 'float32',       
        'Seguro': 'float32', 
        'Enganche_Simulado': 'float32', 
        'Enganche_Min': 'float32', 
        'Enganche_Max': 'float32'}

    financial_cols_to_load = list(dtypes.keys())

    # Dataframe Financiero resultado del Enricher.
    df_financial = pd.read_csv(financial_csv_path, encoding='utf-8', usecols=lambda c: c in financial_cols_to_load, dtype=dtypes)
    df_financial = financial_data_calculation(df_financial)
    
    df_kavak_cards = pd.read_json(kavak_cards_json_path, encoding='utf-8', lines=True)
    df_merged = data_merge(df_financial, df_kavak_cards)

    # Casting to 
    df_merged['Año'] = df_merged['Año'].astype('Int64')
    df_merged['Km'] = df_merged['Km'].astype('Int64')

    df_merged.to_csv('../data/processed/csv/2026_01_10-11_30.csv', encoding='utf-8', index=False)


if __name__ == '__main__':
    main()


