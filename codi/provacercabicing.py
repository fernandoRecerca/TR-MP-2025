
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
    print("Estació:", station["name"])
    print("   -> Bicis lliures:", station["free_bikes"])
    print("   -> Espais lliures:", station["empty_slots"])
    print("-" * 40)
