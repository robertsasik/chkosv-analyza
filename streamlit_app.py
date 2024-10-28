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
    db_connection_url = f"postgresql://{user}:{password}@{host}:{port}/chko_sv_analyza"
    engine = create_engine(db_connection_url)
    engine.dispose() 
    return engine

#Volanie funkcie pomocou premennej con
con = get_db_connection()

#SQL dopyt pomocou premennej sql
sql = "SELECT * FROM chko_sv_vlastnictvo_v;"
sql_m = "SELECT * FROM mapa_vlastnictvo_v;"

#Pužitie geopandas na volanie relačnej tabuľky z PostgreSQL+Postgis databázy
gdf = gpd.read_postgis(sql_m, con, geom_col='geom', crs = 5514)

tab = pd.read_sql_query(sql, con)
st.dataframe(tab)

#Zobrazenie interaktívnej tabuľky
st.dataframe(gdf)

st.write("Došiel som sem.")

