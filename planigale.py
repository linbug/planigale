from urllib.request import urlopen
import json

url = 'http://eol.org/api/pages/1.0/1045608.json?images=2&videos=0&sounds=0&maps=0&text=2&iucn=false&subjects=overview&licenses=all&details=true&common_names=true&synonyms=true&references=true&vetted=0&cache_ttl='
response = urlopen(url)
data = str(response.read().decode('utf-8'))
page = json.loads(data)

# images_list = [objects.get('mediaURL') for objects in page['dataObjects'] if objects.get('mediaURL') is not None]

common_name = [name['vernacularName'] for name in page['vernacularNames'] if name['language'] == 'en' and name.get('eol_preferred') == True][0]
# print(images_list)
print(common_name)