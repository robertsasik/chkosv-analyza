import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from sqlalchemy import create_engine
from streamlit_folium import st_folium
from PIL import Image
import plotly.graph_objects as go


# Nastavenie layoutu na celú šírku stránky
st.set_page_config(layout="wide")

######################### dashboard - prvý riadok a dva stĺpce #########################

row1_col1, row1_col2 = st.columns([1, 7])

with row1_col1:
    image = Image.open("data/strazovske_vrchy.png")
    st.image(image, use_column_width=False) 
    
with row1_col2:
    st.write("### Chránená krajinná oblasť Strážovské vrchy")
    st.write("####  Analýza vlastníckych vzťahov")

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

#Definovanie farebnej mapy pre jednotlivé formy vlastníctva a pre zobrazenie mapy

ownership_colors = {
    "cirkevné": "#7d3c98", #"cirkevné"
    "miest, obcí, samosprávneho kraja": "#2980b9", #"miest, obcí, samosprávneho kraja"
    "spoločenstvenné": "#e74c3c", #"spoločenstvenné"
    "súkromné": "#935116", #"súkromné"
    "štátne": "#28b463", #"štátne"
    "nezistené": "#f1c40f", #"nezistené"       
    }

######################### dashboard - druhý riadok a dva stĺpce #########################

row2_col1, row2_col2, = st.columns([6, 3])  # Pomery stĺpcov, 5:2(ľavý:pravy)
with row2_col1:
    
    st.write("###### Tab.: výmery pozemkov v ha podľa formy vlastníctva a druhu pozemkov")
    
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
    st.dataframe(pivot_table, use_container_width=True)  # Prispôsobenie šírky tabuľky
    

with row2_col2:
    
    data = pd.DataFrame(tab)
    
    # Vytvorenie rolovacieho menu pre výber typu grafu
    chart_type = st.selectbox("",["Percentuálny podiel výmer pozemkov podľa formy vlastníctva", "Výmery pozemkov podľa formy vlastníctva"])

    if chart_type == "Percentuálny podiel výmer pozemkov podľa formy vlastníctva":
        
        # Vytvorenie koláčového grafu s dierou (donut graf)
        fig = go.Figure(data=[go.Pie(
            labels=data["Forma vlastníctva"],
            values=data["Celková plocha (ha)"],
            hole=0.4,
            marker=dict(colors=[
                ownership_colors["cirkevné"],
                ownership_colors["miest, obcí, samosprávneho kraja"],
                ownership_colors["spoločenstvenné"],
                ownership_colors["súkromné"],
                ownership_colors["štátne"],
                ownership_colors["nezistené"]
            ])
        )])

        # Pridanie názvu grafu
        fig.update_layout()

        # Zobrazenie grafu v Streamlit s prispôsobením šírky
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Výmery pozemkov podľa formy vlastníctva":
       
        # Usporiadanie dát od najväčšej po najmenšiu hodnotu
        data_sorted = data.sort_values(by="Celková plocha (ha)", ascending=False)

        # Vytvorenie stĺpcového grafu
        fig = go.Figure(data=[
            go.Bar(
                x=data_sorted["Forma vlastníctva"],  # Na osi X sú názvy vlastností
                y=data_sorted["Celková plocha (ha)"],  # Na osi Y sú hodnoty
                marker=dict(
                    color=[
                        ownership_colors["spoločenstvenné"],
                        ownership_colors["súkromné"],
                        ownership_colors["štátne"],
                        ownership_colors["miest, obcí, samosprávneho kraja"],
                        ownership_colors["cirkevné"],
                        ownership_colors["nezistené"]  
                    ][:len(data_sorted)] # Zabezpečiť, že farby sú v rozsahu
                )
            )
        ])

        # Pridanie názvu grafu a popisov osí
        fig.update_layout(
            #title_text="Percentuálny podiel vlastníckych vzťahov",
            xaxis_title="Forma vlastníctva",
            yaxis_title="Celková plocha (ha)",
        )

        # Zobrazenie grafu v Streamlit s prispôsobením šírky
        st.plotly_chart(fig, use_container_width=True)


########################### koniec - druhý riadok a dva stĺpce ##########################
legend_html = f"""
    <div style="background: white; padding: 0px; font-size: 14px;">
        <h6 style="margin: 0;">Legenda</h6>
        <div style="display: flex; flex-wrap: wrap; gap: 10px; align-items: center;">
            <div style="display: inline-flex; align-items: center; margin-right: 10px;">
                <div style="background-color: {ownership_colors["štátne"]}; width: 20px; height: 20px; margin-right: 5px; opacity: 0.5;"></div>
                <span>Štátne</span>
            </div>
            <div style="display: inline-flex; align-items: center; margin-right: 10px;">
                <div style="background-color: {ownership_colors["miest, obcí, samosprávneho kraja"]}; width: 20px; height: 20px; margin-right: 5px; opacity: 0.5;"></div>
                <span>Miest, obcí, samosprávneho kraja</span>
            </div>
            <div style="display: inline-flex; align-items: center; margin-right: 10px;">
                <div style="background-color: {ownership_colors["súkromné"]}; width: 20px; height: 20px; margin-right: 5px; opacity: 0.5;"></div>
                <span>Súkromné</span>
            </div>
            <div style="display: inline-flex; align-items: center; margin-right: 10px;">
                <div style="background-color: {ownership_colors["spoločenstvenné"]}; width: 20px; height: 20px; margin-right: 5px; opacity: 0.5;"></div>
                <span>Spoločenstvenné</span>
            </div>
            <div style="display: inline-flex; align-items: center; margin-right: 10px;">
                <div style="background-color: {ownership_colors["cirkevné"]}; width: 20px; height: 20px; margin-right: 5px; opacity: 0.5;"></div>
                <span>Cirkevné</span>
            </div>
            <div style="display: inline-flex; align-items: center; margin-right: 10px;">
                <div style="background-color: {ownership_colors["nezistené"]}; width: 20px; height: 20px; margin-right: 5px; opacity: 0.5;"></div>
                <span>Nezistené</span>
            </div>
        </div>
    </div>
    <br>
"""
   
# Pridanie legendy do Streamlit ako HTML
st.markdown(legend_html, unsafe_allow_html=True)

#st.write(f"Mapa vlastníckych vzťahov na území CHKO Strážovské vrchy: {legenda}")



# Deklarácia štýlovej funkcie s farbami podľa formy vlastníctva
def style_function(feature):
    ownership_type = feature['properties'].get("Forma vlastníctva", "nezistené")
    color = ownership_colors.get(ownership_type, "#f1c40f")  # Default farba pre 'nezistené'
    return {
            'fillColor': color,
            'color': 'black',
            'weight': 0.1,  # Nastavenie hrúbky obrysu
            'fillOpacity': 0.5,  # Priehľadnosť výplne
            'opacity': 0.6  # Priehľadnosť obrysu
        }
    # Vytvorenie interaktívnej mapy
m = folium.Map(location=[49.04519085530501, 18.45598270193193], zoom_start=11)
    
# Pridanie GeoDataFrame vrstvy na mapu so zvoleným štýlom
folium.GeoJson(gdf, style_function=style_function, name = "Forma vlastnictva").add_to(m)
    
# Pridanie rôznych basemáp
folium.TileLayer("Esri.WorldShadedRelief", name="Esri Shaded Relief").add_to(m)
folium.TileLayer("OpenTopoMap", name="OpenTopo Map").add_to(m)
folium.TileLayer("Esri.WorldTopoMap", name="Esri Topo Map").add_to(m)

# Pridanie prepínača na ovládanie vrstiev
folium.LayerControl().add_to(m)
    
# Zobrazenie interaktívnej mapy v Streamlit
st_folium(m, width=None, height=780)  # Nastavenie šírky a výšky mapy




