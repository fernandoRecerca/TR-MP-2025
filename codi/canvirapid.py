import requests

# URL de CityBikes per Bicing (Barcelona)
url = "https://api.citybik.es/v2/networks/bicing"

# Fem la crida
response = requests.get(url)
if response.status_code != 200:
    print("Error en la connexió:", response.status_code)
    exit()

data = response.json()

# Recorrem totes les estacions
for station in data["network"]["stations"]:
    bicis = station["free_bikes"]
    espais = station["empty_slots"]

    # El canvi més ràpid en una estació és el mínim entre bicis i espais
    canvi_rapid = min(bicis, espais)

    print("Estació:", station["name"])
    print("   -> Bicis lliures:", bicis)
    print("   -> Espais lliures:", espais)
    print("   -> Canvis ràpids possibles:", canvi_rapid)
    print("-" * 40)
