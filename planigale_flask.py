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

# Get app secret key for sessions from environment variable
# MUST be manually set to run on server, but random key is OK locally
app.secret_key =  os.getenv('PLANIGALE_KEY',os.urandom(24))

# Get redis URL from environment variable
# MUST be manually set to run on server OR locally
redis_url = os.getenv('REDIS_URL')

# configure logging if not running debug
if app.debug != True:
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
    timeout = 60 * 15 # timeout in seconds

    if game is not None:
        g._redis.set(name=g._sid, value=game.to_json(), ex=timeout)


def get_game():
    app.logger.debug("Getting game in redis w/ SID ({}).".format(g._sid))
    json_text = g._redis.get(g._sid)
    game = None
    if json_text is not None:
        game = PlanigaleGame.from_json(json_text.decode("utf-8"))

    app.logger.debug("{}".format(game))

    return game


def get_species_data():
    app.logger.debug("Getting species data..")
    data = getattr(g, '_species_data', None)

    if data is None:
        species = g._species_data = Planigale.load_species_from_json()

    return species


def get_redis():
    app.logger.debug("Getting connection pool for redis sever: {}".format(redis_url))

    return redis.from_url(redis_url)


def get_new_session():
    app.logger.debug("Getting new session..")
    return uuid4()


def get_session_id():
    app.logger.debug("Getting session ID")
    if 'id' not in session:
        session['id'] = get_new_session()

    app.logger.debug("Session # {} accessed.".format(session['id']))
    return session['id']


@app.before_request
def before():
    app.logger.debug("Running before()")
    # get redis connection, set it to the g variable
    g._redis = get_redis()

    # get the request ID if it doesn't exist
    g._sid = get_session_id()

    # get the game and set it to the g variable
    g._game = get_game()


@app.after_request
def after(response):
    app.logger.debug("Starting after()")
    # set the game from the g variable to redis
    set_game(g._game)

    return response


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

        data = get_species_data()
        g._game = PlanigaleGame(data, total_questions, num_hints)
        set_game(g._game)

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
    # Get the game and re-route if not set
    game = g._game
    if game is None:
        # flash("Please start a game first!")
        return redirect(url_for('index'))

    # get the user's choice
    try:
        choice = int(request.form["choice"])
    except(Exception):
        flash("Please select a species name!")
        return redirect(url_for('question'))

    # validate the user's guess
    guess_species = game.curr_question.species[choice]
    game.score_question(game.curr_question, guess_species)

    # set and pass variables for use in template
    validation = "correct" if game.curr_question.correct else "incorrect"
    question = game.curr_question
    choices = zip(question.species, question.species_text, question.species_thumb)

    return render_template('answer.html',
                           question_num = game.question_num,
                           total_questions = game.total_questions,
                           question = game.curr_question,
                           validation = validation,
                           choices = choices)


@app.route('/next', methods=['POST'])
def next():
    # Get the game and re-route if not set
    game = g._game
    if game is None:
        # flash("Please start a game first!")
        return redirect(url_for('index'))

    # Get the next question or route to summary when complete
    if game.next_question():
        return redirect(url_for('question'))
    else:
        return redirect(url_for('summary'))


@app.route('/summary', methods=['GET'])
def summary():
    # Get the game and re-route if not set
    game = g._game
    if game is None:
        # flash("Please start a game first!")
        return redirect(url_for('index'))

    # Re-route to current question if quiz is not completed yet
    if game.question_num != game.total_questions and game.curr_question.guess is None:
        flash("Please finish the quiz first!")
        return redirect(url_for('question'))
    else:
        # Set the variables to pass to the template for rendering
        choices = []
        for question in game.questions:
            choices.append(zip(question.species, question.species_text, question.species_thumb))

        questions = zip (game.questions, choices)

        return render_template('summary.html',
                               game = game,
                               questions = questions)


if __name__ == '__main__':
    # run in debug mode if run directly from console
    app.run(debug=True)
