from datetime import datetime
import pandas as pd
import numpy as np
import requests
import json
from tqdm import tqdm
from time import sleep
import os
import dotenv
dotenv.load_dotenv()
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import warnings
warnings.filterwarnings("ignore")

def abrir_web(ciudad, pagina, fecha1, fecha2):

    """
    Abre una página web de Civitatis para una ciudad específica y un rango de fechas, y devuelve el contenido HTML de la página.

    Parámetros:
    ciudad (str): Nombre de la ciudad en la URL de la página web.
    pagina (int): Número de la página a consultar.
    fecha1 (str): Fecha de inicio del rango (formato YYYY-MM-DD).
    fecha2 (str): Fecha de fin del rango (formato YYYY-MM-DD).

    Retorna:
    BeautifulSoup: Objeto BeautifulSoup que contiene el HTML de la página web.
    """
        
    driver = webdriver.Chrome()

    url = f"https://www.civitatis.com/es/{ciudad}/?pagina={pagina}&fromDate={fecha1}&toDate={fecha2}"
    driver.get(url)
    driver.maximize_window()

    try:
        # Esperamos a que aparezca el filtro para que la pagina carge bien
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'a-filter--applied')))
    except Exception as e:
        print(f"Ha habido un error esperando la página: {e}")
    
    sleep(1)

    contenido_html = driver.page_source
    sopa = BeautifulSoup(contenido_html, 'html.parser')
    
    driver.close()

    return sopa

def extraer_actividades_civitatis(ciudad, fecha1, fecha2):
    """
    Extrae actividades turísticas de la página de Civitatis para una ciudad y rango de fechas específicos.

    Para cada actividad, se extraen el nombre, la puntuación, el precio, la descripción y el enlace.

    Parámetros:
    ciudad (str): Nombre de la ciudad en la URL de la página web.
    fecha1 (str): Fecha de inicio del rango (formato YYYY-MM-DD).
    fecha2 (str): Fecha de fin del rango (formato YYYY-MM-DD).

    Retorna:
    dict: Un diccionario que contiene los siguientes campos:
        - 'Nombre': Lista de nombres de las actividades.
        - 'Puntuación': Lista de puntuaciones de las actividades.
        - 'Precio': Lista de precios de las actividades.
        - 'Descripción': Lista de descripciones de las actividades.
        - 'Link': Lista de enlaces a las actividades.
    

    """
    nombres = []
    puntuaciones = []
    precios = []
    descripciones = []
    links = []

    for pagina in tqdm(range(1, 7)):
        sopa = abrir_web(ciudad, pagina, fecha1, fecha2)
        categorias = sopa.findAll('div', {'class': 'o-search-list__item'})
        for categoria in categorias:
            
            try:
                nombres.append(categoria.find('h2', {"class": "comfort-card__title"}).text.strip())
            except:
                nombres.append(np.nan)
            try:
                puntuaciones.append(categoria.find('span', {"class": "m-rating--text"}).text.replace('/ 10', '').replace(',', '.').strip())    
            except:
                puntuaciones.append(np.nan)
            try:
                precios.append(categoria.find('span', {"class": "comfort-card__price__text"}).text.replace('€', '').strip())
            except:
                precios.append(np.nan)    
            try:
                descripciones.append(categoria.find('div', {"class": "comfort-card__text l-list-card__text"}).text.replace('\xa0',' ').strip())
            except:
                descripciones.append(np.nan)
            try:
                links.append(f"https://www.civitatis.com{categoria.find('a', {'class': 'ga-trackEvent-element _activity-link'}).get('href')}")
            except:
                links.append(np.nan)
        sleep(2)
    diccionario_categorias = {'Nombre': nombres, 'Puntuación': puntuaciones, 'Precio': precios, 'Descripción': descripciones, 'Link': links}
    
    return diccionario_categorias

def crear_df_actividades(ciudad, fecha1, fecha2):
    """
    Crea un DataFrame con las actividades turísticas extraídas de la página de Civitatis para una ciudad y rango de fechas específicos.

    Parámetros:
    ciudad (str): Nombre de la ciudad para buscar las actividades.
    fecha1 (str): Fecha de inicio del rango (formato YYYY-MM-DD).
    fecha2 (str): Fecha de fin del rango (formato YYYY-MM-DD).

    Retorna:
    DataFrame: Un DataFrame que contiene las actividades extraídas, con columnas como 'Nombre', 'Puntuación', 'Precio', 'Descripción' y 'Link'.
    """
    df_civitatis = pd.DataFrame(extraer_actividades_civitatis(ciudad, fecha1, fecha2))
    pd.set_option('display.max_colwidth', None)
    return df_civitatis


def convertir_columnas_a_float(df, columnas):
    """
    Convierte las columnas especificadas de un DataFrame de string a float.

    Parámetros:
    df (DataFrame): El DataFrame a modificar.
    columnas (list): Lista de nombres de las columnas que se desea convertir a float.

    Retorna:
    DataFrame: El DataFrame con las columnas convertidas.
    """
    for columna in columnas:
        # Intentamos convertir la columna a float, si falla se deja como NaN
        df[columna] = pd.to_numeric(df[columna], errors='coerce')
    
    return df



