from urllib.request import urlopen
from io import BytesIO
import json
import random
from PIL import Image
import os
import pickle

def get_url(url):
    '''get json page data using a specified eol API url'''
    response = urlopen(url)
    data = str(response.read().decode('utf-8'))
    page = json.loads(data)
    return page

def load_data(pickle_file='species.pickle'):
    try:
        with open(pickle_file, 'rb') as f:
            data = pickle.load(f)
    except (Exception):
        data = fetch_data()
    return data

def fetch_data(pickle_file='species.pickle', num_species=10):
    search_url = 'http://eol.org/api/collections/1.0/55422.json?page=1&per_page={}&filter=&sort_by=richness&sort_field=&cache_ttl='.format(num_species)

    #ping the API to get the json data for these pages
    results = get_url(search_url)

    #create a species list that contains the object ID for each species in the top500
    species_ID_list = [item['object_id'] for item in results['collection_items']]

    data = [Species.from_eolid(ID) for ID in species_ID_list]

    with open(pickle_file, 'wb') as f:
        pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)

    return data

class Question(object):
    def __init__(self, data):
        self.species = random.sample(data,3)
        self.answer = random.choice(self.species)
        self.picture = random.choice(self.answer.images_list)
        self.guess = None
        self.correct = None

    def verify(self, guess_species):
        if self.guess == None:
            self.guess = guess_species
        else:
            return
        self.correct = (guess_species == self.answer)

        return self.correct

class Game(object):
    def __init__(self, data, total_questions):
        self.score = 0
        self.question_number = 1
        self.total_questions = total_questions
        self.questions = [Question(data) for i in range(self.total_questions)]

    def play(self):
        for question_num, question in enumerate(self.questions, start=1):
            os.system('clear')
            print("\nQuestion {}.".format(question_num))
            self.display_question(question)
            self.get_guess(question)
            if (question_num == self.total_questions):
                input("Press enter to see your summary!")
            else:
                input("Press enter to continue to the next question!")
        self.display_final_score()

    def display_question(self, question):
        response = urlopen(question.picture)
        img = Image.open(BytesIO(response.read()))
        img.show()

        for choice_num, species in enumerate(question.species, start = 1):
            print("{}. {}".format(choice_num, species.scientific_name))

    def get_guess(self, question):
            guess = input("What species is in this picture? Enter a choice between 1 and {}: ".format(self.total_questions))
            while True:
                try:
                    guess_species = question.species[int(guess)-1]
                    break
                except (NameError, TypeError, SyntaxError, IndexError) :
                    guess = input("Not a valid choice! Enter a choice between 1 and {}".format(self.total_questions))
            if question.verify(guess_species):
                self.score += 1
                print("You guessed correctly! Your score is {}.".format(self.score))
            else:
                print("You guessed incorrectly! The correct answer was {}.".format(question.answer))

    def display_final_score(self):
        os.system('clear')
        print("You got {} out of {} questions correct!".format(self.score, self.total_questions))

        print("\nLet's review the questions and answers!")
        for question_num, question in enumerate(self.questions,start=1):
            print("\n\nQuestion {}.".format(question_num))
            for species_num, species in enumerate(question.species,start=1):
                print("{}. {}".format(species_num, species))
            print("\nAnswer was {}.".format(question.answer))

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

if __name__ == '__main__':
    data = load_data()

    new_game = Game(data,3)

    new_game.play()
