import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import geopandas as gpd
import plotly.express as px
import folium
from streamlit_folium import st_folium

# Načítanie skrytých premenných z Streamlit Secrets
host = st.secrets["db_host"]
port = int(st.secrets["db_port"])
database = st.secrets["db_database"]
user = st.secrets["db_user"]
password = st.secrets["db_password"]

@st.cache_resource
def get_db_connection():
    # Vytvorenie URL pre pripojenie k databáze
    db_connection_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    try:
        # Pokus o vytvorenie pripojenia
        engine = create_engine(db_connection_url)
        
        # Test pripojenia vykonaním jednoduchého dotazu
        with engine.connect() as connection:
             connection.execute("SELECT * FROM;")
        
        st.success("Pripojenie k databáze bolo úspešne nadviazané!")
        return engine
    
    except OperationalError as e:
        st.error(f"Pripojenie k databáze zlyhalo: {e}")
    
    finally:
        # Ak je engine vytvorený, uvoľníme pripojenie
        if 'engine' in locals():
            engine.dispose()
            st.write("Pripojenie bolo ukončené.")

# Volanie funkcie a uloženie pripojenia do premennej 'con'
con = get_db_connection()




