import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

# Nastavenie názvu dashboardu
st.set_page_config(page_title="Rozdelený Dashboard", layout="wide")

# Príkladové údaje pre grafy a tabuľku
data = pd.DataFrame({
    "Kategória": ["A", "B", "C", "D"],
    "Hodnota": [25, 15, 35, 25],
    "Mesto": ["Bratislava", "Košice", "Prešov", "Žilina"],
    "Koordináty": [(48.14816, 17.10674), (48.7164, 21.2611), (49.0000, 21.2333), (49.2230, 18.7395)]
})

# Layout pre hornú časť dashboardu s dvoma stĺpcami
col1, col2 = st.columns([2, 3])

with col1:
# Koláčový graf s prispôsobenou veľkosťou
    st.write("### Koláčový graf")
    pie_chart = px.pie(data, names="Kategória", values="Hodnota", title="Podiely podľa kategórií")
    pie_chart.update_layout(width=300, height=300)  # Nastavenie šírky a výšky grafu
    st.plotly_chart(pie_chart, use_container_width=False)  # Nastavenie 'use_container_width=False' kvôli fixným rozmerom

    # Stĺpcový graf s prispôsobenou veľkosťou
    st.write("### Stĺpcový graf")
    bar_chart = px.bar(data, x="Kategória", y="Hodnota", title="Hodnoty podľa kategórií")
    bar_chart.update_layout(width=400, height=300)  # Nastavenie šírky a výšky grafu
    st.plotly_chart(bar_chart, use_container_width=False)

    
    # Spodná časť dashboardu s interaktívnou tabuľkou
    st.write("### Interaktívna tabuľka")
    st.dataframe(data, width=600, height=300)  # Nastavenie šírky na 600px a výšky na 300px

with col2:
    # Interaktívna mapa
    st.write("### Interaktívna mapa")
    m = folium.Map(location=[48.5, 19.0], zoom_start=7)  # Centroid Slovenska
    for _, row in data.iterrows():
        folium.Marker(
            location=row["Koordináty"],
            popup=f"{row['Mesto']}: {row['Hodnota']}%",
            tooltip=row["Mesto"]
        ).add_to(m)
    st_folium(m, width=600, height=900)




