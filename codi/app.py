import streamlit as st
import subprocess
import os

st.set_page_config(page_title="Bicing vs AMBici", layout="wide")

st.title("🚲 Anàlisi en temps real: Bicing i AMBici")

st.write("Aquesta pàgina web permet executar el programa final i visualitzar els resultats directament des del navegador.")

#Paràmetres d'execució
st.sidebar.header("Opcions")
top_n = st.sidebar.number_input("Nombre d'estacions TOP", min_value=1, max_value=50, value=10)
sumari = st.sidebar.checkbox("Mostrar resum global", value=True)
transbord = st.sidebar.checkbox("Detectar punts de transbord", value=True)

#Construcció de la comanda
cmd = ["python3", "programafinal.py", "--top", str(top_n)]
if sumari:
    cmd.append("--sumari")
if transbord:
    cmd.append("--transbord")

#Executar programa
if st.button("Executar programa"):
    st.write("### Resultats del programa:")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        st.code(result.stdout)
    except subprocess.CalledProcessError as e:
        st.error("Error en l'execució del programa")
        st.code(e.stderr)

#Mostrar imatges generades
st.write("### Figures generades")
col1, col2, col3 = st.columns(3)

if os.path.exists("map_estacions.png"):
    col1.image("map_estacions.png", caption="Mapa estacions")
if os.path.exists("map_transbords.png"):
    col2.image("map_transbords.png", caption="Mapa transbords")
if os.path.exists("compare_bicis.png"):
    col3.image("compare_bicis.png", caption="Comparativa de recursos")

#Mostrar CSV
if os.path.exists("resum_estacions.csv"):
    import pandas as pd
    df = pd.read_csv("resum_estacions.csv")
    st.write("### Dades resum")
    st.dataframe(df)
    
    # Descarregar CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Descarregar CSV", csv, "resum_estacions.csv", "text/csv")

