import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from sqlalchemy import create_engine
from streamlit_folium import st_folium
from PIL import Image

# Nastavenie layoutu na celú šírku stránky
st.set_page_config(layout="wide")

# Prvý "riadok" s dvomi stĺpcami
row1_col1, row1_col2 = st.columns([1, 5])

with row1_col1:
    image = Image.open("data/strazovske_vrchy.gif") 
    st.image(image, use_column_width=False)
    
    
with row1_col2:
    st.title("Rozšírený Streamlit Dashboard")
    st.write("Toto je popis dashboardu.")

# Vytvorenie skrytých premenných na pripojenie do databázy
host = st.secrets["db_host"]
port = int(st.secrets["db_port"])
database = st.secrets["db_database"]
user = st.secrets["db_user"]
password = st.secrets["db_password"]

# Funkcia na vytvorenie databázového spojenia
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

# Rozdelenie na tri stĺpce
col1, col2, col3 = st.columns([2, 1, 1])  # Pomery stĺpcov, 2:1:1 (ľavý:pravy:legendový)

# Tabuľka na ľavej strane
with col1:
    st.subheader("Tabuľka údajov")
    st.dataframe(tab)

# Mapa na pravej strane
with col2:
    # Definovanie farebnej mapy pre jednotlivé formy vlastníctva
    ownership_colors = {
        "štátne": "#28b463",
        "miest, obcí, samosprávneho kraja": "#2980b9",
        "súkromné": "#935116",
        "spoločenstvenné": "#e74c3c",
        "cirkevné": "#7d3c98",
        "nezistené": "#f1c40f"
    }

    # Deklarácia štýlovej funkcie s farbami podľa formy vlastníctva
    def style_function(feature):
        ownership_type = feature['properties'].get('Forma vlastníctva', 'nezistené')
        color = ownership_colors.get(ownership_type, "#f1c40f")  # Default farba pre 'nezistené'
        return {
            'fillColor': color,
            'color': 'black',
            'weight': 0.1,  # Nastavenie hrúbky obrysu
            'fillOpacity': 0.5,  # Priehľadnosť výplne
            'opacity': 0.6  # Priehľadnosť obrysu
        }

    # Vytvorenie interaktívnej mapy pomocou knižnice folium do objektu m
    m = folium.Map(location=[49.04519085530501, 18.45598270193193], zoom_start=10, tiles="OpenTopoMap")  #CartoDB positron

    # Pridanie GeoDataFrame vrstvy na mapu so zvoleným štýlom
    folium.GeoJson(gdf, style_function=style_function).add_to(m)

    # Zobrazenie interaktívnej mapy v Streamlit
    st_folium(m, width=300, height=600)

# Legenda na pravej strane
with col3:
    #st.subheader("Legenda")
    # HTML pre legendu bez fixného pozicionovania
    legend_html = """
    <div style="background: white; padding: 0px; font-size: 12px;">
        <h6 style="margin: 0;">Forma vlastníctva</h6>
        <div style="display: flex; align-items: center;">
            <div style="background-color: #28b463; width: 20px; height: 20px; margin-right: 5px; opacity: 0.5;"></div>
            <span>Štátne</span>
        </div>
        <div style="display: flex; align-items: center;">
            <div style="background-color: #2980b9; width: 20px; height: 20px; margin-right: 5px; opacity: 0.5;"></div>
            <span>Miest, obcí, samosprávneho kraja</span>
        </div>
        <div style="display: flex; align-items: center;">
            <div style="background-color: #935116; width: 20px; height: 20px; margin-right: 5px; opacity: 0.5;"></div>
            <span>Súkromné</span>
        </div>
        <div style="display: flex; align-items: center;">
            <div style="background-color: #e74c3c; width: 20px; height: 20px; margin-right: 5px; opacity: 0.5;"></div>
            <span>Spoločenstvenné</span>
        </div>
        <div style="display: flex; align-items: center;">
            <div style="background-color: #7d3c98; width: 20px; height: 20px; margin-right: 5px; opacity: 0.5;"></div>
            <span>Cirkevné</span>
        </div>
        <div style="display: flex; align-items: center;">
            <div style="background-color: #f1c40f; width: 20px; height: 20px; margin-right: 5px; opacity: 0.5;"></div>
            <span>Nezistené</span>
        </div>
    </div>
    """
    
    # Pridanie legendy do Streamlit ako HTML
    st.markdown(legend_html, unsafe_allow_html=True)

st.write("Došiel som sem.")
