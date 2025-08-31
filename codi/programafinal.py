"""
Programa per consultar estacions de Bicing i AMBici i trobar punts de transbord.

Funcionalitats:
  - Consulta dades de CityBikes (Bicing) i GBFS JSON (AMBici)
  - Filtre per barri o per coordenades + radi
  - Ordena per "canvi ràpid" (mínim entre bicis lliures i espais lliures)
  - Cerca punts de transbord entre les dues xarxes
  - Opció d'exportar resultats en CSV
"""

import argparse
import csv
import sys
import math
import requests
from typing import List, Dict, Any


# URLs d’API

API_BICING = "https://api.citybik.es/v2/networks/bicing"
API_AMBICI_INFO = "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_bs/ca/station_information.json"
API_AMBICI_STATUS = "https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_bs/ca/station_status.json"


# DESCÀRREGA DE DADES


def obtenir_dades_bicing(timeout: int = 10) -> List[Dict[str, Any]]:
    """Descarrega les dades de Bicing via CityBikes."""
    try:
        resp = requests.get(API_BICING, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        sys.exit(f"Error connectant a Bicing: {e}")

    if "network" not in data or "stations" not in data["network"]:
        sys.exit("Error: format inesperat de la resposta de Bicing.")

    estacions = []
    for st in data["network"]["stations"]:
        bicis = st.get("free_bikes") or 0
        espais = st.get("empty_slots") or 0
        canvi_rapid = min(bicis, espais)
        estacions.append(
            {
                "servei": "Bicing",
                "id": st.get("id"),
                "nom": st.get("name", "(sense nom)"),
                "lat": st.get("latitude"),
                "lon": st.get("longitude"),
                "bicis_lliures": bicis,
                "espais_lliures": espais,
                "canvi_rapid": canvi_rapid,
            }
        )
    return estacions


def obtenir_dades_ambici(timeout: int = 10) -> List[Dict[str, Any]]:
    """Descarrega les dades d'AMBici via GBFS (Nextbike)."""
    try:
        info = requests.get(API_AMBICI_INFO, timeout=timeout).json()
        status = requests.get(API_AMBICI_STATUS, timeout=timeout).json()
    except requests.exceptions.RequestException as e:
        sys.exit(f"Error connectant a AMBici: {e}")

    stations_info = {st["station_id"]: st for st in info["data"]["stations"]}
    stations_status = {st["station_id"]: st for st in status["data"]["stations"]}

    estacions = []
    for sid, st in stations_info.items():
        estat = stations_status.get(sid, {})
        bicis = estat.get("num_bikes_available", 0)
        espais = estat.get("num_docks_available", 0)
        canvi_rapid = min(bicis, espais)
        estacions.append(
            {
                "servei": "AMBici",
                "id": sid,
                "nom": st.get("name", "(sense nom)"),
                "lat": st.get("lat"),
                "lon": st.get("lon"),
                "bicis_lliures": bicis,
                "espais_lliures": espais,
                "canvi_rapid": canvi_rapid,
            }
        )
    return estacions



# DISTÀNCIA ENTRE PUNTS

def distancia_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distància en metres (fórmula de Haversine)."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))



# FILTRATGE D’ESTACIONS

def filtrar_estacions(estacions: List[Dict[str, Any]], args: argparse.Namespace) -> List[Dict[str, Any]]:
    """Filtra per barri o per coordenades+radi."""
    result = estacions

    if args.barri:
        txt = args.barri.lower()
        result = [e for e in result if txt in e["nom"].lower()]

    if args.coords and args.radi:
        lat0, lon0 = args.coords
        result = [
            e for e in result
            if e["lat"] and e["lon"] and distancia_m(lat0, lon0, e["lat"], e["lon"]) <= args.radi
        ]

    return result



# CERCA DE PUNTS DE TRANSBORD

def punts_transbord(bicing: List[Dict[str, Any]], ambici: List[Dict[str, Any]], radi: float = 250):
    """Busca parelles d’estacions Bicing ↔ AMBici properes (< radi)."""
    punts = []
    for b in bicing:
        for a in ambici:
            if b["lat"] and a["lat"]:
                d = distancia_m(b["lat"], b["lon"], a["lat"], a["lon"])
                if d <= radi:
                    punts.append((b, a, int(d)))
    return punts


def filtrar_transbords(punts: List, args: argparse.Namespace) -> List:
    """Filtra punts de transbord per coords+radi (si s'ha especificat)."""
    if not (args.coords and args.radi):
        return punts

    lat0, lon0 = args.coords
    result = []
    for b, a, d in punts:
        # Punt mig entre estacions de transbord
        latm = (b["lat"] + a["lat"]) / 2
        lonm = (b["lon"] + a["lon"]) / 2
        if distancia_m(lat0, lon0, latm, lonm) <= args.radi:
            result.append((b, a, d))
    return result



# MOSTRAR RESULTATS

def imprimir_estacions(estacions: List[Dict[str, Any]], sumari: bool) -> None:
    """Mostra info de cada estació i un resum opcional."""
    for e in estacions:
        print(f"[{e['servei']}] {e['nom']}")
        print(f"   → Bicis lliures: {e['bicis_lliures']}")
        print(f"   → Espais lliures: {e['espais_lliures']}")
        print(f"   → Canvi ràpid possible: {e['canvi_rapid']}")
        print("-" * 40)

    if sumari:
        total_bicis = sum(e["bicis_lliures"] for e in estacions)
        total_espais = sum(e["espais_lliures"] for e in estacions)
        total_canvi = sum(e["canvi_rapid"] for e in estacions)
        print("Resum global")
        print(f"   Estacions: {len(estacions)}")
        print(f"   Bicis lliures totals: {total_bicis}")
        print(f"   Espais lliures totals: {total_espais}")
        print(f"   Canvi ràpid total: {total_canvi}")


def imprimir_transbords(punts: List, limit: int = None):
    """Mostra punts de transbord entre xarxes."""
    if not punts:
        print("No s’han trobat punts de transbord.")
        return

    print("\nPunts de transbord Bicing ↔ AMBici:")
    for i, (b, a, d) in enumerate(sorted(punts, key=lambda x: x[2])):
        if limit and i >= limit:
            break
        print(f"- {b['nom']} (Bicing) ↔ {a['nom']} (AMBici) [{d} m]")



# EXPORTAR CSV

def desar_csv(estacions: List[Dict[str, Any]], path: str) -> None:
    """Desa les dades en CSV."""
    camps = ["servei", "id", "nom", "lat", "lon", "bicis_lliures", "espais_lliures", "canvi_rapid"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=camps)
        w.writeheader()
        for e in estacions:
            w.writerow(e)



# ARGUMENTS DE LÍNIA DE COMANDES

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Consulta estacions de Bicing i AMBici, i punts de transbord")
    p.add_argument("--top", "-t", type=int, default=None, help="Mostra només les N estacions amb més canvi ràpid")
    p.add_argument("--output", "-o", type=str, default=None, help="Fitxer CSV de sortida")
    p.add_argument("--timeout", type=int, default=10, help="Timeout de la petició HTTP (s)")
    p.add_argument("--sumari", action="store_true", help="Mostra resum global al final")
    p.add_argument("--barri", type=str, default=None, help="Filtra per nom de barri (subcadena)")
    p.add_argument("--coords", type=float, nargs=2, metavar=("LAT", "LON"), help="Coordenades centrals per filtrar")
    p.add_argument("--radi", type=float, default=None, help="Radi en metres per filtrar (quan hi ha coords)")
    p.add_argument("--transbord", action="store_true", help="Mostra punts de transbord Bicing ↔ AMBici")
    return p.parse_args()



# MAIN

def main() -> None:
    args = parse_args()

    # Obtenim dades de les dues xarxes
    bicing = obtenir_dades_bicing(args.timeout)
    ambici = obtenir_dades_ambici(args.timeout)

    # Juntem totes les estacions
    totes = bicing + ambici

    # Apliquem filtres
    totes = filtrar_estacions(totes, args)

    # Ordenem per canvi ràpid
    totes.sort(key=lambda e: (e["canvi_rapid"], e["bicis_lliures"]), reverse=True)

    # Limitem a top N si cal
    a_mostrar = totes
    if args.top:
        a_mostrar = totes[: args.top]

    # Mostrem estacions
    imprimir_estacions(a_mostrar, args.sumari)

    # Mostrem punts de transbord si es demana
    if args.transbord:
        transbords = punts_transbord(bicing, ambici, radi=250)
        transbords = filtrar_transbords(transbords, args)  # <<< nou filtre
        imprimir_transbords(transbords, limit=args.top)

    # Desa CSV si cal
    if args.output:
        desar_csv(totes, args.output)
        print(f"\nCSV desat a: {args.output}")


if __name__ == "__main__":
    main()

