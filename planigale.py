from urllib.request import urlopen
from io import BytesIO
import json
import random
from PIL import Image
import os
import pickle
import jsonpickle
import re
import html
import copy

class Planigale(object):
    @staticmethod
    def get_url(url):
        '''get json page data using a specified eol API url'''
        response = urlopen(url)
        data = str(response.read().decode('utf-8'))
        page = json.loads(data)
        return page

    @staticmethod
    def fetch_species(num_species=10):
        search_url = 'http://eol.org/api/collections/1.0/55422.json?page=1&per_page={}&filter=&sort_by=richness&sort_field=&cache_ttl='.format(num_species)

        print("Pickled species data not found.")
        print("Fetching species list from EOL Collection API..")

        #ping the API to get the json data for these pages
        results = Planigale.get_url(search_url)
        print("Received {} results.".format(len(results['collection_items'])))

        #create a species list that contains the object ID for each species in results
        species_id_list = [item['object_id'] for item in results['collection_items']]

        print("Fetching species details from Pages API..")
        species_data = {}
        for sid in species_id_list:
              try:
                  print("Processing EOL ID# {}".format(sid))
                  s = Species.from_eolid(sid)
                  species_data[sid] = s
                  print("Initialized species: {}".format(s))
              except Exception as ex:
                  print("Exception {} was encountered while loading EOL ID {}.".format(ex, sid))
        # species = list(filter(None, species))
        print("Finished processing species details with {} species in final results.".format(len(species_data)))

        return species_id_list, species_data

    @staticmethod
    def load_species_from_pickle(data_file='species.pickle', num_species=10):
        try:
            with open(data_file, 'rb') as f:
                species_data = pickle.load(f)
            sid_list = list(species_data.keys())
        except (Exception):
            sid_list, species_data = Planigale.fetch_species(num_species=num_species)
            Planigale.save_pickle(data_file, species_data)
        return sid_list, species_data

    @staticmethod
    def save_pickle(pickle_file, data):
        with open(pickle_file, 'wb') as f:
            print("Writing pickle to {}.".format(pickle_file))
            pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def load_species_from_json(data_file='species.json', num_species=10):
        try:
            with open(data_file, 'r') as f:
                json_text = f.read()
                data = json.loads(json_text)
                sid_list = []
                species_data = {}
                for sid, item in data.items():
                    sid_list.append(sid)
                    species_data[sid] = Species(**item)
        except Exception as ex:
            sid_list, species_data = Planigale.fetch_species(num_species=num_species)
            Planigale.save_json(data_file, species_data)
            print("Exception: {}".format(ex))
        return sid_list, species_data

    @staticmethod
    def save_json(json_file, data):
        json_text = jsonpickle.encode(data, unpicklable=False)
        with open(json_file, 'w') as f:
            f.write(json_text)

    @staticmethod
    def load_species_from_redis(redis, sid_list=None):
        '''This function will load species from the provided list of sid.
        Species will be deserialized from json.
        '''
        species_data = {}
        # could get all values in one shot..
        # json_list = redis.mget(sid_list)
        for sid in sid_list:
            json_text = redis.get(':'.join(['species',sid])).decode('utf-8')
            data = json.loads(json_text)
            species_data[sid] = Species(**data)
        return species_data

    def save_redis(redis, data, entity='species'):
        # Update the list for all keys for the entity
        # Update each value for the entity keys
        for key, val in data.items():
            redis_key = ':'.join([entity,key])
            json_text = jsonpickle.encode(val, unpicklable=False)
            print("Adding key {} to redis..".format(redis_key))
            redis.sadd(entity, key)
            redis.set(redis_key, json_text)

    @staticmethod
    def get_sid_list_from_redis(redis, num_species=10):
        '''This function will get a random list of sid from redis set
        Using this function:
        http://redis.io/commands/srandmember
        '''
        bytes_list = redis.srandmember('species',num_species)
        sid_list = []
        for x in bytes_list:
            sid_list.append(x.decode('utf-8'))
        return sid_list


class PlanigaleGame(object):
    def __init__(self,
                 species_data=None,
                 total_questions=3,
                 num_hints=0,
                 score=0,
                 hints_remaining=None,
                 questions=None,
                 question_num=1):
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

    @staticmethod
    def from_json(json_text):
        game_data = json.loads(json_text)

        game = PlanigaleGame(**game_data)

        return game

    def to_json(self):
        json_text = jsonpickle.encode(self, unpicklable=False)

        return json_text

    def score_question(self, guess_species, hints=0):
        question = self.questions[self.question_num-1]

        if question.verify(guess_species):
            self.score += 1
        return question.correct

    def next_question(self):
        if self.question_num < self.total_questions:
            self.question_num += 1
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
                 num_choices=3,
                 species=None,
                 answer=None,
                 revealed_hint=False,
                 guess=None,
                 correct=None):
        # what is required:
        # picture, thumb, scientific name & common name for each choice..
        # index for answer?
        # text for answer
        # or ID for each one.. fetch from DB

        # species should contain a list of sid for the number of choices
        if species is None:
            self.species = []
            for s in range(num_choices):
                sid = random.choice(list(species_data.keys()))
                species_data.pop(sid)
                self.species.append(sid)
        else:
            self.species = species

        # answer should contain an sid for the answer species
        if answer is None:
            self.answer = random.choice(self.species)
        else:
            self.answer = answer

        # revealed hint will be true or false depending on if hint has been used
        self.revealed_hint = revealed_hint

        # guess will equal to the sid of the guessed species
        if guess is None:
            self.guess = None
        else:
            self.guess = guess

        # corrrect will be true or false depending on the user's response
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
                 picture='',
                 thumb='',
                 text='',
                 web_url='http://eol.org',
                 sid=None):
        self.scientific_name = scientific_name
        self.common_name = common_name
        self.picture = picture
        self.thumb = thumb
        self.text = text
        self.web_url = web_url
        self.sid = sid

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
       ''' Make a deep copy of the species object
       '''
       species_copy = cls(scientific_name=species.scientific_name,
                          common_name=species.common_name,
                          text=species.text,
                          picture=species.picture,
                          thumb=species.thumb,
                          web_url=species.web_url)
       return species_copy

    @classmethod
    def from_eolid(cls, eolid):
        '''Creates a Species class from a provided EOL ID.
        This will connect to the Encyclopedia of life Pages API and
        extract/transform/load the required data from the API.
        '''

        url = 'http://eol.org/api/pages/1.0/{}.json?images=2&videos=0&sounds=0&maps=0&text=2&iucn=false&subjects=overview&licenses=all&details=true&common_names=true&synonyms=true&references=true&vetted=0&cache_ttl='.format(eolid)

        page = Planigale.get_url(url)

        # get name data
        scientific_name = page['scientificName']
        common_name = ''
        for name in page['vernacularNames']:
            if name['language'] == 'en' and \
               name.get('eol_preferred') == True:
                common_name = name['vernacularName']
                break

        # TODO - clean parens in name data
        # scientific_name = ' '.join(scientific_name.split()[:2]) + ' (' + \
        #                     ' '.join(scientific_name.replace('(', '').replace(')', '').split()[2:]) + ')'

        # Get text and picture data
        images = []
        text = []
        thumbs = []
        for objects in page['dataObjects']:
            mime_type = objects.get('mimeType').split('/')[0] \
                        if objects.get('mimeType') else None
            media_url = objects.get('eolMediaURL')
            thumb_url = objects.get('eolThumbnailURL')
            lang = objects.get('language')
            description = objects.get('description')
            if media_url is not None and mime_type == 'image':
                images.append(media_url)
                thumbs.append(thumb_url)
            elif description is not None and mime_type == 'text' and lang == 'en':
                # Remove HTML tags and escape sequences
                desc = re.sub('<[^<]+?>', '',
                              description
                              .replace("</p>", '/n').
                              split('/n')[0])
                desc = html.unescape(desc)
                text.append(desc)

        # build eol web url
        web_url = 'http://www.eol.org/pages/' + str(page.get('identifier'))

        # validate the key fields
        has_names = scientific_name is not None and common_name is not None
        has_images = len(images)
        has_text = len(text)
        is_species = False
        for taxon in page['taxonConcepts']:
            if taxon.get('taxonRank') == 'Species':
                is_species = True
                break

        if has_names and has_images and has_text and is_species:
            return cls(scientific_name=scientific_name,
                       common_name=common_name,
                       picture=images[0],
                       thumb=thumbs[0],
                       text=text[0],
                       web_url=web_url,
                       sid=eolid)
        else:
            raise Exception("has_names={}; Has_images={}; Has_text={}; is_species={}".format(
                has_names, has_images, has_text, is_species))

    def __repr__(self):
        return "{s} ({c})".format(c=self.common_name, s=self.scientific_name)


class PlanigaleConsole(object):
    def __init__(self, species_data, total_questions=3, num_hints=0):
        self.species_data = copy.deepcopy(species_data)
        self.game = PlanigaleGame(species_data, total_questions=total_questions, num_hints=0)

    def play(self):
        for question_num, question in enumerate(self.game.questions, start=1):
            self.display_question(question, question_num)
            guess_species = self.get_guess(question)
            self.check_guess(question, guess_species)
            self.display_break(question_num)
        self.display_final_score()

    def display_break(self, question_num):
        if (not self.game.next_question()):
            input("\nPress enter to see your summary!")
        else:
            input("\nPress enter to continue to the next question!")

    def display_question(self, question, question_num, hints=0):
        os.system('clear')
        print("Question {}.".format(question_num))
        try:
            picture = self.species_data[question.answer].picture
            response = urlopen(picture)
            img = Image.open(BytesIO(response.read()))
            img.show()
        except Exception as ex:
            print(ex)

        for choice_num, species in enumerate(question.species, start = 1):
            scientific_name = self.species_data[species].scientific_name
            print("{}. {}".format(choice_num, scientific_name))

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
        answer = self.species_data[question.answer]
        if self.game.score_question(guess_species, hints=hints_used):
            print("\nYou guessed correctly! Your score is {}.".format(self.game.score))
        else:
            print("\nYou guessed incorrectly! The correct answer was {}.".format(answer))


        print("\nSpecies description: {}".format(answer.text))


    def display_final_score(self):
        os.system('clear')
        print("You got {} out of {} questions correct!".format(self.game.score, self.game.total_questions))

        print("\nLet's review the questions and answers!")
        for question_num, question in enumerate(self.game.questions,start=1):
            print("\n\nQuestion {}.".format(question_num))
            for species_num, species in enumerate(question.species,start=1):
                print("{}. {}".format(species_num, self.species_data[species]))
            print("\nYour answer was {}, which was {}.".format(
                self.species_data[question.guess], 'Correct' if question.correct else 'Incorrect'))
            print("\nAnswer was {}.".format(self.species_data[question.answer]))


if __name__ == '__main__':
    sid_list, species_data = Planigale.load_species_from_json(num_species=500)
    console = PlanigaleConsole(species_data)
    # console.play()
