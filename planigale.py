from urllib.request import urlopen
from io import BytesIO
import json
import random
from PIL import image

def get_url(url):
	response = urlopen(url)
	data = str(response.read().decode('utf-8'))
	page = json.loads(data)
	return page

search_url = 'http://eol.org/api/collections/1.0/55422.json?page=1&per_page=50&filter=&sort_by=richness&sort_field=&cache_ttl='

top500 = get(search_url)
species_list = [item['object_id'] for item in top500['collection_items']]

random_list = random.sample(species_list,3)

class Species(object):
	def __init__(self, scientific_name, common_name, images_list):
		self.scientific_name = scientific_name
		self.common_name = common_name
		self.images_list = images_list

	def show_image(self):
		response = urlopen(random.choice(self.images_list))
		img = Image.open(BytesIO(response.read()))
		img.show()

    @classmethod
    def from_eolid(cls, eolid):
    	url = 'http://eol.org/api/pages/1.0/{}.json?images=2&videos=0&sounds=0&maps=0&text=2&iucn=false&subjects=overview&licenses=all&details=true&common_names=true&synonyms=true&references=true&vetted=0&cache_ttl='.format(eolid)

		images_list = [objects.get('mediaURL') for objects in page['dataObjects'] 
						if objects.get('mediaURL') is not None]

		scientific_name = page['scientific_name']

		common_name = [name['vernacularName'] for name in page['vernacularNames'] 
						if name['language'] == 'en' and name.get('eol_preferred') == True][0]

		return cls(scientific_name, common_name, images_list)

	def __repr__(self):
		return "{c} ({s})".format(c=common_name, s=scientific_name)
