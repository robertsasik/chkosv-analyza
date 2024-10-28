import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import geopandas as gpd
import plotly.express as px
import folium
from streamlit_folium import st_folium

#Vytvorenie skrytých premenných na pripojenie do databázy
host = st.secrets["db_host"]
port = int(st.secrets["db_port"])
database = st.secrets["db_database"]
user = st.secrets["db_user"]
password = st.secrets["db_password"]

@st.cache_resource #dekorátor pripojenia na databázové zdroje

#Vytvorenie funkcie na pripojenie na databázu
def get_db_connection():
    db_connection_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    engine = create_engine(db_connection_url)
    engine.dispose() 
    return engine

#Volanie funkcie pomocou premennej con
con = get_db_connection()

st.write("Dosiel som sem")



