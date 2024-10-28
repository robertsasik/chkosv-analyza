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
    return engine

#Volanie funkcie pomocou premennej con
con = get_db_connection()

#SQL dopyt pomocou premennej sql
sql = "SELECT * FROM vztahy_vlastnictvo;"
sql_m = "SELECT * FROM mapa_vlastnictvo;"

#Pužitie geopandas na volanie relačnej tabuľky z PostgreSQL+Postgis databázy
gdf = gpd.read_postgis(sql_m, con, geom_col='geom', crs = 5514)

tab = pd.read_sql_query(sql, con)
st.dataframe(tab)

#Zobrazenie interaktívnej tabuľky
#st.dataframe(gdf)

#Konverzia súradnicového systému S-JTSK na WGS-84 pomocou geopandas
gdf = gdf.to_crs(epsg=4326)

# Definovanie farebnej mapy pre jednotlivé formy vlastníctva
ownership_colors = {
    "štátne": "#3186cc",
    "miest, obcí, samosprávneho kraja": "#32a852",
    "súkromné": "#e377c2",
    "spoločenstvenné": "#ff7f0e",
    "cirkevné": "#ff7f0e",
    "nezistené": "#d62728"
}

# Deklarácia štýlovej funkcie s farbami podľa formy vlastníctva
def style_function(feature):
    ownership_type = feature['properties'].get('Forma vlastníctva', 'nezistené')
    color = ownership_colors.get(ownership_type, "#d62728")  # Default farba pre 'nezistene'
    return {
        'fillColor': color,
        'color': 'black',
        'weight': 0,
        'fillOpacity': 0.6,
    }

#Vytvorenie interaktívnej mapy pomocou knižnice folium do objektu m
m = folium.Map(location=[49.128173785261644, 18.42754307767109], zoom_start=12) 

# Pridanie GeoDataFrame vrstvy na mapu so zvoleným štýlom
folium.GeoJson(gdf, style_function=style_function).add_to(m)

# Zobrazenie interaktívnej mapy v Streamlit
st_folium(m, width=800, height=600)

# Uzatvorenie pripojenia na konci skriptu
con.dispose()

st.write("Došiel som sem.")

