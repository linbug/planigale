from urllib.request import urlopen
from io import BytesIO
import json
import random
from PIL import Image
import os
import pickle

class Planigale(object):
    @staticmethod
    def get_url(url):
        '''get json page data using a specified eol API url'''
        response = urlopen(url)
        data = str(response.read().decode('utf-8'))
        page = json.loads(data)
        return page

    @staticmethod
    def load_species(pickle_file='species.pickle'):
        try:
            with open(pickle_file, 'rb') as f:
                data = pickle.load(f)
        except (Exception):
            data = fetch_species()
        return data

    @staticmethod
    def fetch_species(pickle_file='species.pickle', num_species=10):
        search_url = 'http://eol.org/api/collections/1.0/55422.json?page=1&per_page={}&filter=&sort_by=richness&sort_field=&cache_ttl='.format(num_species)

        #ping the API to get the json data for these pages
        results = get_url(search_url)

        #create a species list that contains the object ID for each species in the top500
        species_ID_list = [item['object_id'] for item in results['collection_items']]

        species = []
        for ID in species_ID_list:
            species.append(Species.from_eolid(ID))
        data = filter(None, data)

        with open(pickle_file, 'wb') as f:
            pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)

        return species

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

class PlanigaleGame(object):
    def __init__(self, data, total_questions=3, hints=0):
        self.score = 0
        self.question_number = 1
        self.total_questions = total_questions
        self.hints = 0
        self.questions = [Question(data) for i in range(self.total_questions)]

    def score_question(self, question, guess_species, hints=0):
        if question.verify(guess_species):
            self.score += 1

class PlanigaleConsole(object):
    def __init__(self, data, total_questions=3, hints=0):
        self.game = PlanigaleGame(data, total_questions=3, hints=0)
        self.play(self.game)

    def play(self, game):
        for question_num, question in enumerate(self.game.questions, start=1):
            self.display_question(question, question_num)
            guess_species = self.get_guess(question)
            self.check_guess(question, guess_species)
            self.display_break(question_num)
        self.display_final_score()

    def display_break(self, question_num):
        if (question_num == self.game.total_questions):
            input("\nPress enter to see your summary!")
        else:
            input("\nPress enter to continue to the next question!")

    def display_question(self, question, question_num, hints=0):
        os.system('clear')
        print("Question {}.".format(question_num))
        try:
            response = urlopen(question.picture)
            img = Image.open(BytesIO(response.read()))
            img.show()
        except(Exception):
            question.picture = 'http://s7.postimg.org/dlar2hyfv/planigale_missing.jpg'
            response = urlopen(question.picture)
            img = Image.open(BytesIO(response.read()))
            img.show()
            question.answer = Species('Planigale maculata', 'Planigale', question.picture)
            question.species = [question.answer] * 3

        for choice_num, species in enumerate(question.species, start = 1):
            print("{}. {}".format(choice_num, species.scientific_name))

    def get_guess(self, question):
        #todo - entering 0 or negative numbers will break this..
        guess = input("\nWhat species is in this picture? Enter a choice between 1 and {}: ".format(len(question.species)))
        while True:
            try:
                guess_species = question.species[int(guess)-1]
                break
            except (Exception):
                guess = input("Not a valid choice! Enter a choice between 1 and {}: ".format(len(question.species)))

        return guess_species

    def check_guess(self, question, guess_species, hints_used=0):
        if self.game.score_question(question, guess_species, hints=hints_used):
            print("\nYou guessed correctly! Your score is {}.".format(self.score))
        else:
            print("\nYou guessed incorrectly! The correct answer was {}.".format(question.answer))

    def display_final_score(self):
        os.system('clear')
        print("You got {} out of {} questions correct!".format(self.game.score, self.game.total_questions))

        print("\nLet's review the questions and answers!")
        for question_num, question in enumerate(self.game.questions,start=1):
            print("\n\nQuestion {}.".format(question_num))
            for species_num, species in enumerate(question.species,start=1):
                print("{}. {}".format(species_num, species))
            print("\nYour answer was {}, which was {}.".format(
                question.guess, 'Correct' if question.correct else 'Incorrect'))
            print("\nAnswer was {}.".format(question.answer))

class Species(object):
    '''Creates a new species object that stores scientific name, common name and images\
    from an eol page '''

    def __init__(self, scientific_name, common_name, images_list):
        self.scientific_name = scientific_name
        self.common_name = common_name
        self.images_list = images_list
        # print("Initialized species: {}".format(self))

    def show_image(self):
        response = urlopen(random.choice(self.images_list))
        img = Image.open(BytesIO(response.read()))
        img.show()

    @classmethod
    def from_eolid(cls, eolid):
        '''class method that creates a Species class from a provided eol ID'''

        url = 'http://eol.org/api/pages/1.0/{}.json?images=2&videos=0&sounds=0&maps=0&text=2&iucn=false&subjects=overview&licenses=all&details=true&common_names=true&synonyms=true&references=true&vetted=0&cache_ttl='.format(eolid)

        page = get_url(url)

        images_list = []
        for objects in page['dataObjects']:
            if objects.get('eolMediaURL') is not None and \
               objects.get('mimeType')[:5] == 'image':
                images_list.append(objects.get('eolMediaURL'))

        scientific_name = page['scientificName']

        common_name = ''
        for name in page['vernacularNames']:
            if name['language'] == 'en' and \
               name.get('eol_preferred') == True:
                common_name = name['vernacularName']
                break

        # validate the key fields (don't give back a Species if they're not true):
        has_images = len(images_list)
        is_species = page['taxonConcepts']['taxonRank'] == 'Species'

        if has_images and is_species:
            return cls(scientific_name, common_name, images_list)

    def __repr__(self):
        return "{c} ({s})".format(c=self.common_name, s=self.scientific_name)

if __name__ == '__main__':
    data = Planigale.load_species()
    PlanigaleConsole(data)
