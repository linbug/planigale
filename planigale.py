from urllib.request import urlopen
from io import BytesIO
import json
import random
from PIL import Image
import os
import pickle
import jsonpickle
import re

class Planigale(object):
    @staticmethod
    def get_url(url):
        '''get json page data using a specified eol API url'''
        response = urlopen(url)
        data = str(response.read().decode('utf-8'))
        page = json.loads(data)
        return page

    @staticmethod
    def fetch_species(pickle_file='species.pickle', num_species=10):
        search_url = 'http://eol.org/api/collections/1.0/55422.json?page=1&per_page={}&filter=&sort_by=richness&sort_field=&cache_ttl='.format(num_species)

        print("Pickled species data not found.")
        print("Fetching species list from EOL Collection API..")

        #ping the API to get the json data for these pages
        results = Planigale.get_url(search_url)
        print("Received {} results.".format(len(results['collection_items'])))

        #create a species list that contains the object ID for each species in results
        species_ID_list = [item['object_id'] for item in results['collection_items']]

        print("Fetching species details from Pages API..")
        species = []
        for ID in species_ID_list:
              try:
                  print("Processing EOL ID# {}".format(ID))
                  s = Species.from_eolid(ID)
                  species.append(s)
                  print("Initialized species: {}".format(s))
              except Exception as ex:
                  print("Exception {} was encountered while loading EOL ID {}.".format(ex, ID))
        species = list(filter(None, species))
        print("Finished processing species details with {} species in final results.".format(len(species)))

        with open(pickle_file, 'wb') as f:
            print("Writing pickle to {}.".format(pickle_file))
            pickle.dump(species, f, pickle.HIGHEST_PROTOCOL)

        return species

    @staticmethod
    def load_species(pickle_file='species.pickle', num_species=500):
        try:
            with open(pickle_file, 'rb') as f:
                species = pickle.load(f)
        except (Exception):
            species = Planigale.fetch_species(pickle_file=pickle_file, num_species=num_species)
        return species

    @staticmethod
    def load_species_from_json(json_file='species.json'):
        try:
            with open(json_file, 'r') as f:
                json_text = f.read()
                data = json.loads(json_text)
                species = []
                for item in data:
                    species.append(Species(**item))

        except Exception as ex:
            print("Exception: {}".format(ex))
        return species



class PlanigaleGame(object):
    def __init__(self,
                 species_data=None,
                 total_questions=3,
                 num_hints=0,
                 score=0,
                 hints_remaining=None,
                 questions=None,
                 question_num=1,
                 curr_question=None):

        self.score = score
        self.num_hints = num_hints

        if hints_remaining is None:
            self.hints_remaining = self.num_hints
        else:
            self.hints_remaining = hints_remaining

        self.total_questions = total_questions

        if questions is None:
            self.questions = [Question(species_data) for i in range(self.total_questions)]
        else:
            self.questions = []
            for q in questions:
                self.questions.append(Question(**q))

        self.question_num = question_num

        if curr_question is None:
            self.curr_question = self.questions[0]
        else:
            # when constructing the question, create reference to entry in question array
            self.curr_question = self.questions[self.question_num-1]

    @staticmethod
    def from_json(json_text):
        game_data = json.loads(json_text)

        game = PlanigaleGame(**game_data)

        return game

    def to_json(self):
        json_text = jsonpickle.encode(self, unpicklable=False)

        return json_text

    def score_question(self, question, guess_species, hints=0):
        if question.verify(guess_species):
            self.score += 1
        return question.correct

    def next_question(self):
        if self.question_num < self.total_questions:
            self.question_num += 1
            self.curr_question = self.questions[self.question_num-1]
            return True
        else:
            return False

    def __repr__(self):
        repr = "Game.\n\n"
        for n, q in enumerate(self.questions, start=1):
            repr += "{}: {}\n\n".format(n, q)

        repr += "Current question {} of {}.\n".format(self.question_num, self.total_questions )
        repr += "Score: {}. Hints remaining: {}.".format(self.score, self.hints_remaining)

        return repr


class Question(object):
    def __init__(self,
                 species_data=None,
                 species=None,
                 species_picture=None,
                 species_thumb=None,
                 species_text=None,
                 answer=None,
                 picture=None,
                 thumb=None,
                 text=None,
                 revealed_hint=False,
                 guess=None,
                 correct=None):
        """Good luck!!!! - Me in the past."""
        if species is None:
            self.species = random.sample(species_data,3)
        else:
            self.species = []
            for s in species:
                self.species.append(Species(**s))


        if species_picture is None or species_thumb is None:
            self.species_picture, self.species_thumb = list(zip(*[random.choice(list(zip(s.images_list, s.thumbs_list))) for s in self.species if s.images_list is not None]))
        else:
            self.species_picture = species_picture
            self.species_thumb = species_thumb

        if species_text is None:
            self.species_text = [random.choice(s.text_list) for s in self.species if s.text_list is not None]
        else:
            self.species_text = species_text

        if answer is None or picture is None or thumb is None or text is None:
            self.answer, self.picture, self.thumb, self.text = random.choice(
                list(zip(self.species, self.species_picture, self.species_thumb, self.species_text)))
        else:
            self.answer = Species(**answer)
            self.picture = picture
            self.thumb = thumb
            self.text = text


        self.revealed_hint = revealed_hint

        if guess is None:
            self.guess = None
        else:
            self.guess = Species(**guess)


        self.correct = correct

    def verify(self, guess_species):
        if self.guess is None:
            self.guess = guess_species
        else:
            return
        self.correct = (guess_species == self.answer)

        return self.correct

    def __repr__(self):
        repr = "Question.\n"
        for n, s in enumerate(self.species, start=1):
            repr += "{}. {}\n".format(n, s)
        repr += "Guess: {}. Correct: {}.".format(self.guess, self.correct)
        return repr


class Species(object):
    '''Creates a new species object that stores scientific name, common name and images\
    from an eol page '''

    def __init__(self,
                 scientific_name='Plangale',
                 common_name='Planigale!',
                 text_list=['Its a planigale.'],
                 images_list=['This is a picture of a planigale.'],
                 thumbs_list=['This is a thumbail of a planigale.'],
                 web_url='http://eol.org'):
        self.scientific_name = scientific_name
        self.common_name = common_name
        self.text_list = text_list
        self.images_list = images_list
        self.thumbs_list = thumbs_list
        self.web_url = web_url

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)

    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_str):
        json_dict = json.loads(json_str)
        return cls(**json_dict)


    def show_image(self):
        response = urlopen(random.choice(self.images_list))
        img = Image.open(BytesIO(response.read()))
        img.show()

    @classmethod
    def from_species(cls, species):
       ''' Make a deep copy of the species object so we can modify the
       current picture and text '''
       species_copy = cls(species.scientific_name, species.common_name, species.text_list, species.images_list, species.thumbs_list, species.web_url)
       species_copy.picture, species_copy.thumb =  random.choice(list(zip(species_copy.images_list, species_copy.thumbs_list))) \
                               if species_copy.images_list is not None else None, None

       species_copy.text = random.choice(species_copy.text_list) \
                           if species_copy.text_list is not None else None
       return species_copy


    @classmethod
    def from_eolid(cls, eolid):
        '''Creates a Species class from a provided EOL ID.
        This will connect to the Encyclopedia of life Pages API and
        extract/transform/load the required data from the API.
        '''

        url = 'http://eol.org/api/pages/1.0/{}.json?images=2&videos=0&sounds=0&maps=0&text=2&iucn=false&subjects=overview&licenses=all&details=true&common_names=true&synonyms=true&references=true&vetted=0&cache_ttl='.format(eolid)

        page = Planigale.get_url(url)

        images = []
        text = []
        thumbs = []
        for objects in page['dataObjects']:
            mime_type = objects.get('mimeType').split('/')[0] \
                        if objects.get('mimeType') else None
            media_url = objects.get('eolMediaURL')
            thumb_url = objects.get('eolThumbnailURL')
            description = objects.get('description')
            if media_url is not None and mime_type == 'image':
                images.append(media_url)
                thumbs.append(thumb_url)
            elif description is not None and mime_type == 'text':
                text.append(re.sub('<[^<]+?>', '',
                                   description
                                   .replace("</p>", '/n').
                                   split('/n')[0]))

        scientific_name = page['scientificName']

        web_url = 'http://www.eol.org/pages/' + str(page.get('identifier'))

        common_name = ''
        for name in page['vernacularNames']:
            if name['language'] == 'en' and \
               name.get('eol_preferred') == True:
                common_name = name['vernacularName']
                break

        # validate the key fields (don't give back a Species if they're not true):
        has_images = len(images)
        has_text = len(text)
        is_species = page['taxonConcepts'][0]['taxonRank'] == 'Species'

        if has_images and has_text and is_species:
            return cls(scientific_name, common_name, text, images, thumbs, web_url)
        else:
            raise Exception("Has_images{}; Has_text={}; is_species={}".format(has_images, has_text, is_species))

    def __repr__(self):
        return "{s} ({c})".format(c=self.common_name, s=self.scientific_name)


class PlanigaleConsole(object):
    def __init__(self, data, total_questions=3, num_hints=0):
        self.game = PlanigaleGame(data, total_questions=3, num_hints=0)

    def play(self):
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
        except Exception as ex:
            print(ex)

        for choice_num, species in enumerate(question.species, start = 1):
            print("{}. {}".format(choice_num, species.scientific_name))

    def get_guess(self, question):
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
            print("\nYou guessed correctly! Your score is {}.".format(self.game.score))
        else:
            print("\nYou guessed incorrectly! The correct answer was {}.".format(question.answer))

        print("\nSpecies description: {}".format(question.text))


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


if __name__ == '__main__':
    data = Planigale.load_species_from_json()
    console = PlanigaleConsole(data)
