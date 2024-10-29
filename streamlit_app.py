import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# Vytvorenie skrytých premenných na pripojenie do databázy
host = st.secrets["db_host"]
port = int(st.secrets["db_port"])
database = st.secrets["db_database"]
user = st.secrets["db_user"]
password = st.secrets["db_password"]

@st.cache_resource  # Dekorátor na kešovanie pripojenia
def get_db_connection():
    db_connection_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    engine = create_engine(db_connection_url)
    return engine

# SQL dopyty pre jednotlivé tabuľky
sql_vlastnictvo = "SELECT * FROM vztahy_vlastnictvo;"
sql_mapa = "SELECT * FROM mapa_vlastnictvo_zl;"

# Funkcia na načítanie dát a konverziu CRS (s kešovaním)
@st.cache_data
def load_data():
    con = get_db_connection()
    
    # Načítanie dát z databázy
    tab = pd.read_sql_query(sql_vlastnictvo, con)
    gdf = gpd.read_postgis(sql_mapa, con, geom_col='geom', crs=5514)
    
    # Konverzia súradnicového systému
    gdf = gdf.to_crs(epsg=4326)
    
    # Uzavretie pripojenia po načítaní dát
    con.dispose()
    
    return tab, gdf

# Načítanie údajov
tab, gdf = load_data()
st.dataframe(tab)

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
    color = ownership_colors.get(ownership_type, "#d62728")  # Default farba pre 'nezistené'
    return {
        'fillColor': color,
        'color': 'black',
        'weight': 0,
        'fillOpacity': 0.6,
    }

# Vytvorenie interaktívnej mapy pomocou knižnice folium do objektu m
m = folium.Map(location=[49.128173785261644, 18.42754307767109], zoom_start=12)

# Pridanie GeoDataFrame vrstvy na mapu so zvoleným štýlom
folium.GeoJson(gdf, style_function=style_function).add_to(m)

# Zobrazenie interaktívnej mapy v Streamlit
st_folium(m, width=800, height=600)

st.write("Došiel som sem.")
