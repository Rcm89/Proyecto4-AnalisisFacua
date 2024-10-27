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

def extraer_informacion_hoteles(respuesta_json):

    """
    Extrae información relevante sobre hoteles a partir de una respuesta JSON de un servicio de búsqueda de hoteles.

    La función itera sobre los resultados del JSON y extrae información clave sobre cada hotel, 
    incluyendo el nombre, número de reseñas, rating, rango de precios, ciudad, servicios ofrecidos y un enlace al hotel.
    Calcula además el precio medio por noche basado en el rango de precios.

    Args:
        respuesta_json (dict): Un diccionario que representa la respuesta en formato JSON de un servicio de búsqueda de hoteles.

    Returns:
        list[dict]: Una lista de diccionarios, donde cada diccionario contiene la información de un hotel con las siguientes claves:
            - nombre: El nombre del hotel.
            - numero_reviews: Número de reseñas del hotel.
            - rating: Rating del hotel.
            - precio_rango_min: El precio mínimo por noche en USD.
            - precio_rango_max: El precio máximo por noche en USD.
            - precio_medio_por noche: Precio medio por noche calculado a partir del rango de precios.
            - ciudad: Ciudad donde se encuentra el hotel.
            - servicios: Lista de servicios que ofrece el hotel.
            - link: URL que enlaza a la página del hotel.
    """
    lista_diccionarios = []
    res = respuesta_json
    for i in range(0, len(res.get("results", []))):

        nombre = res["results"][i].get("name", "N/A")
        numero_reviews = res["results"][i].get("reviews", 0)
        rating = res["results"][i].get("rating", "N/A")
        
        rango_precios = res["results"][i].get("price_range_usd", {})
        precio_rango_min = rango_precios.get("min", 0)
        precio_rango_max = rango_precios.get("max", 0)
        precio_medio = (precio_rango_max + precio_rango_min) / 2 if (precio_rango_max + precio_rango_min) > 0 else 0
        
        ciudad = res["results"][i].get("detailed_address", {}).get("city", "N/A")
        servicios = res["results"][i].get("amenities", [])
        link = res["results"][i].get("link", "N/A")

        diccionario_hotel= {"nombre":nombre,
                "numero_reviews":numero_reviews,
                "rating": rating,
                "precio_rango_min":precio_rango_min,
                "precio_rango_max":precio_rango_max,
                "precio_medio_por noche":precio_medio,
                "ciudad":ciudad,
                "servicios":servicios,
                "link":link
                }
        lista_diccionarios.append(diccionario_hotel)
    return lista_diccionarios

def extraer_informacion_vuelos(respuesta_json):
    """
    Extrae información relevante sobre vuelos a partir de una respuesta JSON de un servicio de itinerarios de vuelos.

    La función itera sobre los vuelos y sus tramos (piernas) en el JSON de respuesta, extrayendo información
    como el precio, aeropuertos de origen y destino, tiempos de salida y llegada, duración del vuelo, escalas y aerolíneas.
    Luego organiza esta información en una lista de diccionarios.

    Args:
        respuesta_json (dict): Un diccionario que representa la respuesta en formato JSON de un servicio de vuelos.

    Returns:
        list[dict]: Una lista de diccionarios, donde cada diccionario contiene la información de un tramo de vuelo con las siguientes claves:
            - id_origen: ID del aeropuerto de origen.
            - ciudad_origen: Nombre de la ciudad de origen.
            - id_destino: ID del aeropuerto de destino.
            - ciudad_destino: Nombre de la ciudad de destino.
            - salida: Hora y fecha de salida del vuelo.
            - llegada: Hora y fecha de llegada del vuelo.
            - duracion(min): Duración del vuelo en minutos.
            - escalas: Número de escalas del vuelo.
            - aerolinea: Nombre de la aerolínea que opera el vuelo.
            - precio: Precio del vuelo (formato raw).
    """
    lista_diccionarios = []
    res = respuesta_json.get("data", {})

    for vuelo in range(0, len(res.get("itineraries", []))): 
        precio = res["itineraries"][vuelo].get("price", {}).get("raw", 0)

        for i in range(0, 2):
            id_origen = res["itineraries"][vuelo]["legs"][i].get("origin", {}).get("id", "N/A")
            origen = res["itineraries"][vuelo]["legs"][i].get("origin", {}).get("city", "N/A")

            id_destino = res["itineraries"][vuelo]["legs"][i].get("destination", {}).get("id", "N/A")
            destino = res["itineraries"][vuelo]["legs"][i].get("destination", {}).get("city", "N/A")

            duracion_minutos = res["itineraries"][vuelo]["legs"][i].get("durationInMinutes", 0)
            escalas = res["itineraries"][vuelo]["legs"][i].get("stopCount", 0)

            salida = res["itineraries"][vuelo]["legs"][i].get("departure", "N/A")
            llegada = res["itineraries"][vuelo]["legs"][i].get("arrival", "N/A")

            aerolinea = res["itineraries"][vuelo]["legs"][i].get("carriers", {}).get("marketing", [{}])[0].get("name", "N/A")

            diccionario_vuelos = {
                "id_origen": id_origen,
                "ciudad_origen": origen,
                "id_destino": id_destino,
                "ciudad_destino": destino,
                "salida": salida,
                "llegada": llegada,
                "duracion(min)": duracion_minutos,
                "escalas": escalas,
                "aerolinea": aerolinea,
                "precio": precio
            }
            lista_diccionarios.append(diccionario_vuelos)
    
    return lista_diccionarios
 


def crear_df_hoteles(funcion_extraer_informacion_hoteles):
    """
    Crea y devuelve un DataFrame a partir de la información de hoteles obtenida.

    La función recibe una lista de diccionarios generada por la función `extraer_informacion_hoteles`, 
    convierte esa lista en un DataFrame y elimina las columnas "precio_rango_min" y "precio_rango_max",
    manteniendo solo la información relevante para el análisis.

    Args:
        funcion_extraer_informacion_hoteles (list[dict]): Lista de diccionarios con información sobre hoteles, 
        obtenida de la función `extraer_informacion_hoteles`.

    Returns:
        pd.DataFrame: Un DataFrame con los datos de hoteles, excluyendo las columnas "precio_rango_min" y "precio_rango_max".
    """

    df_hotel= pd.DataFrame(funcion_extraer_informacion_hoteles).drop(columns= ["precio_rango_min", "precio_rango_max"])
    pd.set_option('display.max_colwidth', None)

    df_hotel
    return df_hotel


def crear_df_vuelos(funcion_informacion_vuelos):
    
    """
    Crea y devuelve un DataFrame a partir de la información de vuelos obtenida.

    La función recibe una lista de diccionarios generada por la función `extraer_informacion_vuelos`, 
    convierte esa lista en un DataFrame y formatea las columnas de "salida" y "llegada" 
    como objetos datetime.

    Args:
        funcion_informacion_vuelos (list[dict]): Lista de diccionarios con información sobre vuelos, 
        obtenida de la función `extraer_informacion_vuelos`.

    Returns:
        pd.DataFrame: Un DataFrame con los datos de vuelos, donde las columnas "salida" y "llegada"
        están formateadas como datetime.
    """

    df_vuelos= pd.DataFrame(funcion_informacion_vuelos)
    df_vuelos["salida"]= pd.to_datetime(df_vuelos["salida"])
    df_vuelos["llegada"]= pd.to_datetime(df_vuelos["llegada"])
    return df_vuelos

