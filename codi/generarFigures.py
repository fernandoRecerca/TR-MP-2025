#!/usr/bin/env python3
"""
genera_figures.py
Crida les APIs de Bicing i AMBici, calcula punts de transbord (<250 m)
i genera 3 imatges PNG per a la memòria:
 - figures/map_estacions.png
 - figures/map_transbords.png
 - figures/compare_bicis.png
"""

import os
import math
import requests
import matplotlib.pyplot as plt
import pandas as pd

# APIs (mateixes que al teu projecte)
API_BICING = "https://api.citybik.es/v2/networks/bicing"
API_AMBICI_INFO = "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_bs/ca/station_information.json"
API_AMBICI_STATUS = "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_bs/ca/station_status.json"

OUT_DIR = "figures"
os.makedirs(OUT_DIR, exist_ok=True)

def distancia_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def obtenir_dades_bicing(timeout=10):
    r = requests.get(API_BICING, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    rows = []
    for st in data["network"]["stations"]:
        lat = st.get("latitude")
        lon = st.get("longitude")
        free = st.get("free_bikes") or 0
        empty = st.get("empty_slots") or 0
        rows.append({
            "servei": "Bicing",
            "id": st.get("id"),
            "nom": st.get("name"),
            "lat": lat,
            "lon": lon,
            "bicis": int(free),
            "espais": int(empty),
            "canvi_rapid": int(min(free, empty))
        })
    return pd.DataFrame(rows)

def obtenir_dades_ambici(timeout=10):
    info = requests.get(API_AMBICI_INFO, timeout=timeout).json()
    status = requests.get(API_AMBICI_STATUS, timeout=timeout).json()
    info_map = {s["station_id"]: s for s in info["data"]["stations"]}
    status_map = {s["station_id"]: s for s in status["data"]["stations"]}
    rows = []
    for sid, st in info_map.items():
        lat = st.get("lat")
        lon = st.get("lon")
        ststat = status_map.get(sid, {})
        bicis = int(ststat.get("num_bikes_available", 0))
        espais = int(ststat.get("num_docks_available", 0))
        rows.append({
            "servei": "AMBici",
            "id": sid,
            "nom": st.get("name"),
            "lat": lat,
            "lon": lon,
            "bicis": bicis,
            "espais": espais,
            "canvi_rapid": int(min(bicis, espais))
        })
    return pd.DataFrame(rows)

def trobar_transbords(df_bicing, df_ambici, radi=250.0):
    punts = []
    # converteix a llistes per velocitat
    b_rows = df_bicing.dropna(subset=["lat","lon"]).to_dict("records")
    a_rows = df_ambici.dropna(subset=["lat","lon"]).to_dict("records")
    for b in b_rows:
        for a in a_rows:
            d = distancia_m(b["lat"], b["lon"], a["lat"], a["lon"])
            if d <= radi:
                punts.append((b, a, int(d)))
    # ordena per distància
    punts.sort(key=lambda x: x[2])
    return punts

def dibuixa_map_estacions(df_bicing, df_ambici, outpath):
    plt.figure(figsize=(10,10))
    # scatter Bicing
    plt.scatter(df_bicing["lon"], df_bicing["lat"], s=10, label="Bicing", alpha=0.7)
    plt.scatter(df_ambici["lon"], df_ambici["lat"], s=10, label="AMBici", alpha=0.7)
    plt.legend()
    plt.title("Estacions Bicing (vermell) i AMBici (blau) - distribució")
    plt.xlabel("Longitud")
    plt.ylabel("Latitud")
    # millora visual: marcar límit aproximat Riera Blanca si vols (opc)
    plt.grid(True, linestyle=":", alpha=0.3)
    plt.savefig(outpath, dpi=200, bbox_inches="tight")
    plt.close()

def dibuixa_transbords(df_bicing, df_ambici, transbords, outpath, n_lines=200):
    plt.figure(figsize=(10,10))
    plt.scatter(df_bicing["lon"], df_bicing["lat"], s=12, label="Bicing", alpha=0.6)
    plt.scatter(df_ambici["lon"], df_ambici["lat"], s=12, label="AMBici", alpha=0.6)
    # dibuixa línies entre parelles (només les primeres n_lines per llegibilitat)
    for i, (b, a, d) in enumerate(transbords):
        if i >= n_lines:
            break
        plt.plot([b["lon"], a["lon"]], [b["lat"], a["lat"]], linewidth=0.8, alpha=0.6)
    plt.legend()
    plt.title(f"Punts de transbord detectats (linies) - max {n_lines}")
    plt.xlabel("Longitud")
    plt.ylabel("Latitud")
    plt.grid(True, linestyle=":", alpha=0.3)
    plt.savefig(outpath, dpi=200, bbox_inches="tight")
    plt.close()

def dibuixa_compartiu(df_bicing, df_ambici, outpath):
    totals = {
        "servei": ["Bicing", "AMBici"],
        "bicis": [df_bicing["bicis"].sum(), df_ambici["bicis"].sum()],
        "espais": [df_bicing["espais"].sum(), df_ambici["espais"].sum()],
        "canvi_rapid": [df_bicing["canvi_rapid"].sum(), df_ambici["canvi_rapid"].sum()]
    }
    df_tot = pd.DataFrame(totals).set_index("servei")
    df_tot.plot(kind="bar", figsize=(8,6))
    plt.title("Comparativa totals: bicis, espais i canvis ràpids")
    plt.ylabel("Nombre")
    plt.xticks(rotation=0)
    plt.grid(axis="y", linestyle=":", alpha=0.3)
    plt.savefig(outpath, dpi=200, bbox_inches="tight")
    plt.close()

def main():
    print("Obtenint dades Bicing...")
    df_b = obtenir_dades_bicing()
    print(f" - estacions Bicing: {len(df_b)}")
    print("Obtenint dades AMBici...")
    df_a = obtenir_dades_ambici()
    print(f" - estacions AMBici: {len(df_a)}")

    print("Calculant punts de transbord (<250 m)...")
    transbords = trobar_transbords(df_b, df_a, radi=250.0)
    print(f" - transbords trobats: {len(transbords)} (limitats per llegibilitat a l'export)")

    print("Generant map_estacions.png ...")
    dibuixa_map_estacions(df_b, df_a, os.path.join(OUT_DIR, "map_estacions.png"))

    print("Generant map_transbords.png ...")
    dibuixa_transbords(df_b, df_a, transbords, os.path.join(OUT_DIR, "map_transbords.png"))

    print("Generant compare_bicis.png ...")
    dibuixa_compartiu(df_b, df_a, os.path.join(OUT_DIR, "compare_bicis.png"))

    print("Figures generades a la carpeta:", OUT_DIR)
    # Guarda també un CSV resum per si vols incloure-lo a annexos
    df_all = pd.concat([df_b, df_a], ignore_index=True)
    df_all.to_csv(os.path.join(OUT_DIR, "resum_estacions.csv"), index=False)
    print("CSV resum guardat:", os.path.join(OUT_DIR, "resum_estacions.csv"))

if __name__ == "__main__":
    main()

