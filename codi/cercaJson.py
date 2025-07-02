import json
import requests

# some JSON:
#x =  '{ "name":"John", "age":30, "city":"New York"}'

# parse x:
#y = json.loads(x)

# the result is a Python dictionary:
#print(y["age"]) 

responseInformation = requests.get('https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_bs/ca/station_information.json')
responseStatus = requests.get('https://gbfs.nextbike.net/maps/gbfs/v2/nextbike_bs/ca/station_status.json')
parsedInformation = responseInformation.json()
parsedStatus = responseStatus.json()

for k in range(0,len(parsedInformation['data']['stations'])):
    print("Estació: ", end="")
    print(parsedInformation['data']['stations'][k]['station_id'])
    print("      ->  Bicis lliures: ", end="")
    print(parsedStatus['data']['stations'][k]['num_bikes_available'])
    print("      ->  Espais lliures: ", end="")
    print(parsedStatus['data']['stations'][k]['num_docks_available'])   
#for k in range(0,len(parsed['station'])):
    #print(parsed['station'][k])

