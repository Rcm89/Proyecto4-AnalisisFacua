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


# Librería para trabajar con bases de datos SQL
import psycopg2
from psycopg2 import OperationalError, errorcodes, errors

def esperar_y_hacer_click_xpath(drivers, ruta_xpath):
    """
    Espera hasta que un elemento esté presente en la página y realiza un clic en él.

    Args:
        drivers (WebDriver): El objeto del navegador (WebDriver) que está siendo utilizado para controlar la página.
        ruta_xpath (str): El XPath del elemento que se está buscando en la página.

    Returns:
        WebElement: El botón o elemento sobre el cual se hizo clic. Retorna `None` si el elemento no se encuentra después de 5 intentos.
    """
    
    boton = None
    intentos = 0
    while True and intentos <= 5:
        try:
            boton = WebDriverWait(drivers, 10).until(EC.presence_of_element_located(("xpath", ruta_xpath)))
            sleep(2)
            boton.click()
            break
        except Exception as e:
            intentos += 1
            print(f"Intento {intentos}: No se ha podido encontrar el botón. Error: {e}")
            continue
    
    return boton

def esperar_y_hacer_click_css(drivers, ruta_css):
    """
    Espera hasta que un elemento esté presente en la página y realiza un clic en él.

    Args:
        drivers (WebDriver): El objeto del navegador (WebDriver) que está siendo utilizado para controlar la página.
        ruta_css (str): El css selector del elemento que se está buscando en la página.

    Returns:
        WebElement: El botón o elemento sobre el cual se hizo clic. Retorna `None` si el elemento no se encuentra después de 5 intentos.
    """
    
    boton = None
    intentos = 0
    while True and intentos <= 5:
        try:
            boton = WebDriverWait(drivers, 10).until(EC.presence_of_element_located(("css selector", ruta_css)))
            sleep(2)
            boton.click()
            break
        except Exception as e:
            intentos += 1
            print(f"Intento {intentos}: No se ha podido encontrar el botón. Error: {e}")
            continue
    
    return boton


def asignar_subcategoria(df_supermercados):
    """
    Asigna una subcategoría a cada producto en función de su categoría y nombre en el DataFrame.

    La función utiliza condiciones para identificar productos específicos (como tipos de aceite de oliva o leche)
    y asignarles una subcategoría relevante en una columna llamada "subcategoria".

    Args:
        df_supermercados (pd.DataFrame): DataFrame que contiene información de productos de supermercado.
                                         Debe tener las columnas 'categoria_producto' y 'nombre_producto'.

    Returns:
        pd.DataFrame: El DataFrame original con una columna adicional 'subcategoria', que contiene
                      el valor de la subcategoría asignada a cada producto según las condiciones especificadas.
                      
                      Valores de subcategoría posibles:
                      - 'virgen extra', 'virgen' (para aceites de oliva)
                      - 'entera', 'semidesnatada', 'desnatada' (para leche)
                      - 'nan' para productos que no cumplan ninguna condición
    """
    
    # Definimos las condiciones y los resultados
    condiciones = [
        (df_supermercados['categoria_producto'] == 'aceite de oliva') & (df_supermercados['nombre_producto'].str.contains('virgen extra', case=False)),
        (df_supermercados['categoria_producto'] == 'aceite de oliva') & (df_supermercados['nombre_producto'].str.contains('virgen', case=False)),
        (df_supermercados['categoria_producto'] == 'leche') & (df_supermercados['nombre_producto'].str.contains('entera', case=False)),
        (df_supermercados['categoria_producto'] == 'leche') & (df_supermercados['nombre_producto'].str.contains('semi|semidesnatada', case=False)),
        (df_supermercados['categoria_producto'] == 'leche') & (df_supermercados['nombre_producto'].str.contains('desnatada', case=False))
    ]


    # Resultados asociados a cada condición
    resultados = ['virgen extra', 'virgen', 'entera', 'semidesnatada', 'desnatada']

    # Asignamos la columna "subcategoria" utilizando np.select
    df_supermercados['subcategoria'] = np.select(condiciones, resultados, default="nan")
    return df_supermercados

def normalizar_cantidad_variacion(variacion):
    variacion = variacion.replace(',','.')
    if variacion.startswith('+'):
        return float(variacion[1:])
    else:
        return float(variacion[1:]) * -1


def conexion_a_dbeaver(database):
    """
    Establece una conexión a una base de datos DBeaver.

    Args:
        database (str): El nombre de la base de datos.

    Returns:
        conexion: Un objeto de conexión a la base de datos.
    """
  
    try:
        conexion = psycopg2.connect(
            database=database,
            user="postgres",
            password=os.getenv("token"),
            host="localhost",
            port="5432"
        )
    except OperationalError as e:
        if e.pgcode == errorcodes.INVALID_PASSWORD:
            print("La contraseña intorducida es errónea")
        elif e.pgcode == errorcodes.CONNECTION_EXCEPTION:
            print("Se ha producido un error de conexión")
        else:
            print(f"Ocurrió el error {e}")
    return conexion

def creacion_tablas(conexion, cursor):
    try:
        # Creación tabla supermercado
        query_creacion_supermercado = '''
            create table if not exists supermercado(
                id_super int primary key,
                nombre VARCHAR(50) not null
            ); '''

        cursor.execute(query_creacion_supermercado)
        conexion.commit()

        # Creación tabla tipo_producto
        query_creacion_tipo_producto = '''
            create table if not exists tipo_producto(
                id_producto int primary key,
                nombre VARCHAR(100) not null
                ); '''

        cursor.execute(query_creacion_tipo_producto)
        conexion.commit()

        # Creación tabla comparativa
        query_creacion_historico = """
            create table if not exists historico (
                id_historico serial primary key,
                id_super integer not null,
                id_producto integer not null,
                nombre varchar(300) not null,
                subcategoria varchar(200),
                fecha date not null,
                precio float,
                variacion float,
                porcentaje float,
                foreign key (id_super) references supermercado(id_super)
                    on update cascade
                    on delete restrict,
                foreign key (id_producto) references tipo_producto(id_producto)
                    on update cascade 
                    on delete restrict
                );"""

        cursor.execute(query_creacion_historico)
        conexion.commit()

    except Exception as e:
        print(f"Error creando tablas: {e}")


def insercion_datos(conexion, cursor, lista_tuplas, query_insercion):
    cursor.executemany(query_insercion, lista_tuplas)
    conexion.commit() 