import json
import requests



request = urllib2.Request('http://opendata-ajuntament.barcelona.cat/data/dataset/8214557a-.../resource/d6b5a09c-.../download/recurs.json')
request.add_header('Authorization', '4f0d4dfaa06a4...')
response = urllib2.urlopen(request)



