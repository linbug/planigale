from flask import Flask, flash, render_template, request, redirect, session, url_for, g
import logging
from logging.handlers import RotatingFileHandler
from planigale import Question, Species, Planigale, PlanigaleGame, PlanigaleConsole
import os
import sys
from uuid import uuid4
import redis
import pickle
import jsonpickle

app = Flask(__name__)

# Get app secret key for sessions from environment
app.secret_key =  os.getenv('PLANIGALE_KEY',os.urandom(24))

# configure logging
handler = RotatingFileHandler('planigale.log', maxBytes=100000, backupCount=10)
std = logging.StreamHandler(sys.stdout)
app.logger.addHandler(std)
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)
app.logger.debug("Starting server.")

# def set_pickle_value(redis, key, value):
#     redis.set(name=key, value=pickle.dumps(value), ex=60*60)


# def get_pickle_value(redis, key):
#     pickled_value = redis.get(key)
#     if pickled_value is None:
#         return None
#     return pickle.loads(pickled_value)


# def set_game_session(game):
#     app.logger.debug("Setting game in session: {}".format(game))
#     if game is not None:
#         session['game'] = game.to_json()

# def get_game_session():
#     if 'game' in session:
#         json_text = session['game']
#         app.logger.debug("Game JSON: {}".format(json_text))

#         game = PlanigaleGame.from_json(json_text)

#         return game
#     else:
#         app.logger.debug("Game not in session")
#         return None


def set_game(game):
    app.logger.debug("Setting game in redis w/ SID ({}).".format(g._sid))
    app.logger.debug("{}".format(game))
    if game is not None:
        g._redis.set(name=g._sid, value=game.to_json(), ex=60*60)


def get_game():
    app.logger.debug("Getting game in redis w/ SID ({}).".format(g._sid))
    json_text = g._redis.get(g._sid)
    game = None
    if json_text is not None:
        game = PlanigaleGame.from_json(json_text.decode("utf-8"))

    app.logger.debug("{}".format(game))

    return game


def get_new_session():
    app.logger.debug("Getting new session..")
    return uuid4()


def get_species_data():
    app.logger.debug("Getting species data..")
    data = getattr(g, '_species_data', None)

    if data is None:
        species = g._species_data = Planigale.load_species_from_json()

    app.logger.debug("Species: {}".format(species[0]))
    return species


def get_redis():
    redis_url=os.getenv('REDIS_URL')
    app.logger.debug("Getting connection pool for redis sever: {}".format(redis_url))
    return redis.from_url(redis_url)


@app.before_request
def before():
    app.logger.debug("Running before()")
    # get redis connection, set it to the g variable
    g._redis = get_redis()

    # get the request ID if it doesn't exist
    g._sid = get_session_id()

    # get the game and set it to the g variable
    g._game = get_game()

    app.logger.debug("finished before(): SID: {}, Game: {}".format(g._sid, g._game))


@app.after_request
def after(response):
    app.logger.debug("Starting after()")
    # set the game from the g variable to redis
    app.logger.debug("Game: {}".format(g._game))
    set_game(g._game)
    app.logger.debug("Finished after()")

    return response


def get_session_id():
    app.logger.debug("Getting session ID")
    if 'id' not in session:
        session['id'] = get_new_session()

    app.logger.debug("Session # {} accessed.".format(session['id']))
    return session['id']


@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
    app.logger.debug("Ready to render index..")
    return render_template('index.html')

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

@app.route('/newgame', methods = ['POST'])
def newgame():
    app.logger.debug("Running newgame")
    try:
        total_questions = int(request.form["num_questions"])

        difficulty_dict = {
            "easy":total_questions,
            "medium": int(total_questions/2),
            "hard": 0
        }

        num_hints = difficulty_dict[request.form["difficulty"]]

        app.logger.debug("Loading data..")
        data = get_species_data()
        app.logger.debug("Loaded data..")
        g._game = PlanigaleGame(data, total_questions, num_hints)
        set_game(g._game)
        app.logger.debug("Created game: {}".format(g._game))

        return redirect(url_for('question'))
    except Exception as ex:
        # flash("Error while creating game. Please retry.")
        app.logger.error("An exception occured while getting newgame: {}".format(ex))
        return redirect(url_for('index'))


@app.route('/question', methods=['POST','GET'])
def question():
    game = g._game

    if game is None:
        # flash("Please start a game first!")
        return redirect(url_for('index'))

    if request.method == 'GET':
        if game.curr_question.guess is not None:
            return redirect(url_for('summary'))

    if request.method == 'POST':
        try:
            if request.form["hint"] == 'True':
                if game.hints_remaining>0:
                    if game.curr_question.revealed_hint == False:
                        game.curr_question.revealed_hint = True
                        game.hints_remaining -= 1
                    else:
                        pass
                elif game.curr_question.revealed_hint == True:
                    pass
                else:
                    flash("Woops! No hints remaining!")
        except(Exception):
            pass

    return render_template('question.html',
        question_num = game.question_num,
        question = game.curr_question,
        total_questions = game.total_questions,
        hints_remaining = game.hints_remaining,
        hint = game.curr_question.revealed_hint )


@app.route('/answer', methods=['POST'])
def answer():
    app.logger.debug('Starting answer()..')
    try:
        choice = int(request.form["choice"])
    except(Exception):
        flash("Please select a species name!")
        return redirect(url_for('question'))

    game = g._game
    guess_species = game.curr_question.species[choice]
    game.score_question(game.curr_question, guess_species)

    validation = "correct" if game.curr_question.correct else "incorrect"

    app.logger.debug("In answer: {}".format(game.curr_question))
    app.logger.debug("In answer: {}.".format(game))

    question = game.curr_question
    choices = zip(question.species, question.species_text, question.species_thumb)
    app.logger.debug("Curr question Types. Species: {}, Text: {}, Thumb: {}.".format(type(question.species), type(question.species_text), type(question.species_thumb)))

    return render_template('answer.html',
                           question_num = game.question_num,
                           total_questions = game.total_questions,
                           question = game.curr_question,
                           validation = validation,
                           choices = choices)


@app.route('/next', methods=['POST'])
def next():
    game = g._game

    if game.next_question():
        return redirect(url_for('question'))
    else:
        return redirect(url_for('summary'))


@app.route('/summary', methods=['GET'])
def summary():
    game = g._game

    if game is None:
        # flash("Please start a game first!")
        return redirect(url_for('index'))
    elif game.question_num != game.total_questions and game.curr_question.guess is None:
        flash("Please finish the quiz first!")
        return redirect(url_for('question'))
    else:
        return render_template('summary.html',
                               game = game)


@app.template_global(name='zip')
def _zip(*args, **kwargs): #to not overwrite builtin zip in globals
    return __builtins__.zip(*args, **kwargs)


if __name__ == '__main__':
    app.run(debug=True)
