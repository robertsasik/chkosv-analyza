import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from sqlalchemy import create_engine
from streamlit_folium import st_folium
from PIL import Image
import plotly.express as px

# Nastavenie layoutu na celú šírku stránky
st.set_page_config(layout="wide")

######################### dashboard - prvý riadok a dva stĺpce #########################

row1_col1, row1_col2 = st.columns([1, 7])

with row1_col1:
    image = Image.open("data/strazovske_vrchy.png")
    st.image(image, use_column_width=False) 
    
with row1_col2:
    st.write("### Chránená krajinná oblasť Strážovské vrchy")
    st.write("####   Analýza vlastníckych vzťahov")

########################### koniec - prvý riadok a dva stĺpce ###########################
st.write("---")

# Vytvorenie skrytých premenných na pripojenie do databázy
host = st.secrets["db_host"]
host = st.secrets["db_host"]
port = int(st.secrets["db_port"])
database = st.secrets["db_database"]
user = st.secrets["db_user"]
password = st.secrets["db_password"]

@st.cache_resource #dekorátor pripojenia na databázové zdroje
# Funkcia na vytvorenie databázového spojenia
def get_db_connection():
    db_connection_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    engine = create_engine(db_connection_url)
    return engine

# SQL dopyty pre jednotlivé tabuľky
sql_vlastnictvo = "SELECT * FROM vztahy_vlastnictvo;"
sql_mapa = "SELECT * FROM mapa_vlastnictvo_zl;"
sql_drp =  "SELECT * FROM mapa_vlastnictvo_drp1;"

# Funkcia na načítanie dát a konverziu CRS (s kešovaním)
@st.cache_data
def load_data():
    con = get_db_connection()
    
    # Načítanie dát z databázy
    tab = pd.read_sql_query(sql_vlastnictvo, con)
    gdf = gpd.read_postgis(sql_mapa, con, geom_col='geom', crs=5514)
    tab_kon = pd.read_sql_query(sql_drp, con)
    # Konverzia súradnicového systému
    gdf = gdf.to_crs(epsg=4326)
    
    # Uzavretie pripojenia po načítaní dát
    con.dispose()
    
    return tab, gdf, tab_kon

# Načítanie údajov
tab, gdf, tab_kon = load_data()

######################### dashboard - druhý riadok a dva stĺpce #########################

row2_col1, row2_col2, = st.columns([5, 2])  # Pomery stĺpcov, 5:2(ľavý:pravy)
with row2_col1:
    
    st.write("Analýza vlastníckych vzťahov podľa kategórií")
    
    #st.dataframe(tab_kon)

    # Vytvorenie pivot tabuľky so špecifikovanými názvami stĺpcov
    pivot_table = pd.pivot_table(
        tab_kon,
        values='Celková plocha (ha)',       # Hodnota, ktorú sumarizujeme
        index='Forma vlastníctva',      # Riadky tabuľky
        columns='Druh pozemku',          # Stĺpce tabuľky
        aggfunc='sum',          # Sumarizačná funkcia, napr. sum
        fill_value=0,            # Náhrada prázdnych hodnôt
        margins=True,            # Pridanie súčtov za riadky a stĺpce
        margins_name='Súčet'     # Názov pre riadok a stĺpec so súčtom
    )
    # Definovanie aliasov pre stĺpce
    aliases = {
        2: 'orná pôda',
        3: 'chmeľnica',
        4: 'vinica',
        5: 'zahrada',
        6: 'ovocný sad',
        7: 'trvalý trávny porast',
        10: 'lesný pozemok',
        11: 'vodná plocha',
        13: 'zastavaná plocha a nádvorie',
        14: 'ostatná plocha',
    }

    # Preformátovanie hodnôt v pivot tabuľke
    # Zmena oddelovača tisícok na medzeru a zaokrúhlenie na 2 desatinné miesta
    pivot_table = pivot_table.applymap(lambda x: f"{x:,.2f}".replace(',', ' ').replace('.', ','))
    
    # Priradenie aliasov stĺpcom
    pivot_table.rename(columns=aliases, inplace=True)

    # Zobrazenie tabuľky v Streamlit
    st.write("Kontingenčná tabuľka")
    st.dataframe(pivot_table, use_container_width=True)  # Prispôsobenie šírky tabuľky


    #st.dataframe(pivot_table)

with row2_col2:
    st.write("Tu budu grafy")
    #st.table(tab)
    data = pd.DataFrame(tab)
    # Farby pre jednotlivé segmenty
    custom_colors = ["#7d3c98", "#2980b9", "#e74c3c", "#935116", "#28b463", "#f1c40f"]

    # Vytvorenie koláčového grafu s dierou (donut graf)
    fig = px.pie(data, 
                names='Forma vlastníctva', 
                values='Celková plocha (ha)', 
                title='Donut graf s vlastnými farbami',
                color_discrete_sequence=custom_colors,
                hole=0.4)  # Parameter hole nastavuje veľkosť diery

    # Zobrazenie grafu
    fig.show()


    

########################### koniec - druhý riadok a dva stĺpce ###########################
st.write("---")

######################### dashboard - tretí riadok a tri stĺpce #########################
# Rozdelenie na tri stĺpce s pevnou výškou
row3_col1, row3_col2, row3_col3 = st.columns([6, 1, 2])  # Pomery stĺpcov, 5:2(ľavý:pravy)

# Mapa na pravej strane
with row3_col1:
    st.markdown('<div class="flexible-height-col">', unsafe_allow_html=True)  # Začiatok divu s flexibilnou výškou
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
    #m = folium.Map(location=[49.04519085530501, 18.45598270193193], zoom_start=11, tiles="Esri.WorldTopoMap") #Esri.WorldShadedRelief, OpenTopoMap

    # Vytvorenie interaktívnej mapy
    m = folium.Map(location=[49.04519085530501, 18.45598270193193], zoom_start=11)
    
    # Pridanie GeoDataFrame vrstvy na mapu so zvoleným štýlom
    folium.GeoJson(gdf, style_function=style_function, name = "Forma vlastnictva").add_to(m)
    
    # Pridanie rôznych basemáp
    folium.TileLayer("OpenTopoMap", name="OpenTopo Map").add_to(m)
    folium.TileLayer("Esri.WorldTopoMap", name="Esri Topo Map").add_to(m)
    folium.TileLayer("Esri.WorldShadedRelief", name="Esri Shaded Relief").add_to(m)

    # Pridanie prepínača na ovládanie vrstiev
    folium.LayerControl().add_to(m)

    # Zobrazenie interaktívnej mapy v Streamlit
    st_folium(m, width=1100, height=780)  # Nastavenie šírky a výšky mapy
    
# Legenda v strednom stlpci
with row3_col2:
    st.markdown('<div class="flexible-height-col">', unsafe_allow_html=True)  # Začiatok divu s flexibilnou výškou
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
    st.markdown('</div>', unsafe_allow_html=True)  # Koniec divu s flexibilnou výškou
    with row3_col3:
        st.write("aaa")

########################### koniec - tretí riadok a tri stĺpce ###########################

st.write("---")
