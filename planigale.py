from urllib.request import urlopen
from io import BytesIO
import json
import random
from PIL import Image

def get_url(url):
    '''get json page data using a specified eol API url'''
    response = urlopen(url)
    data = str(response.read().decode('utf-8'))
    page = json.loads(data)
    return page


class Question(object):
    def __init__(self, data):
        self.species = random.sample(data,3)
        self.answer = random.choice(self.species)
        self.picture = random.choice(self.answer.images_list)
        self.guess = None
        self.correct = None

    def make_guess(self, guess_species):
        if guess == None:
            self.guess = guess_species
        else:
            return

        if guess_species == self.answer:
            self.correct = True
        else:
            self.correct = False

        



    
class Species(object):
    '''Creates a new species object that stores scientific name, common name and images\
    from an eol page '''

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
        '''class method that creates a Species class from a provided eol ID'''

        url = 'http://eol.org/api/pages/1.0/{}.json?images=2&videos=0&sounds=0&maps=0&text=2&iucn=false&subjects=overview&licenses=all&details=true&common_names=true&synonyms=true&references=true&vetted=0&cache_ttl='.format(eolid)

        page = get_url(url)

        images_list = [objects.get('mediaURL') for objects in page['dataObjects']
                        if objects.get('mediaURL') is not None]

        scientific_name = page['scientificName']

        common_name = [name['vernacularName'] for name in page['vernacularNames']
                        if name['language'] == 'en' and name.get('eol_preferred') == True][0]

        return cls(scientific_name, common_name, images_list)

    def __repr__(self):
        return "{c} ({s})".format(c=self.common_name, s=self.scientific_name)

#search url for the eol 'hotlist' collection, first 500 pages sorted by richness
search_url = 'http://eol.org/api/collections/1.0/55422.json?page=1&per_page=500&filter=&sort_by=richness&sort_field=&cache_ttl='

#ping the API to get the json data for these pages
top500 = get_url(search_url)

#create a species list that contains the object ID for each species in the top500
species_ID_list = [item['object_id'] for item in top500['collection_items']]

#create a list of 3 random species IDs
random_list = random.sample(species_ID_list,3)
