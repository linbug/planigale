from flask import Flask, flash, render_template, request, redirect, session, url_for, g
import logging
from logging.handlers import RotatingFileHandler
from planigale import Question, Species, Planigale, PlanigaleGame, PlanigaleConsole
import os

app = Flask(__name__)
app.secret_key =  os.urandom(24)


def get_new_session():
    app.logger.error("Getting new session..")
    curr_session = getattr(g, '_curr_session', None)
    if curr_session is None:
        curr_session = g._curr_session = 0
    else:
        curr_session = g._curr_session = curr_session + 1

    app.logger.error("New session # {} created.".format(curr_session))
    return curr_session

@app.before_first_request
def get_species_data():
    app.logger.error("Getting species data..")
    data = getattr(g, '_species_data', None)
    if data is None:
        data = g._species_data = Planigale.load_species()

    app.logger.error("Loaded {} species.".format(len(data)))
    return data


def get_session_id():
    app.logger.error("Getting session ID")
    if 'id' not in session:
        session['id'] = get_new_session()

    app.logger.error("Session # {} accessed.".format(session['id']))
    return session['id']


def get_game():
    app.logger.error("Getting game")
    id = get_session_id()

    games = getattr(g, '_games', None)
    if games is None:
        games = g._games = {}

    if id not in games:
        games[id] = PlanigaleGame(get_species_data())
        # forward to question for new game?
    game = games[id]

    app.logger.error("Game object loaded for session # {}.".format(id))
    return game


@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/newgame', methods = ['POST'])
def newgame():
    app.logger.error("Running newgame")
    try:
        id = get_session_id()

        total_questions = int(request.form["num_questions"])

        difficulty_dict = {
            "easy":total_questions,
            "medium": int(total_questions/2),
            "hard": 0
        }

        num_hints = difficulty_dict[request.form["difficulty"]]

        games[id] = PlanigaleGame(get_species_data(), total_questions, num_hints)

        return redirect(url_for('question'))
    except Exception as ex:
        flash("Error while creating game. Please retry.")
        app.logger.error("An exception occured while getting newgame: {}".format(ex))
        return redirect(url_for('index'))


@app.route('/question', methods=['POST','GET'])
def question():
    game = get_game()

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
    try:
        choice = int(request.form["choice"])
    except(Exception):
        flash("Please select a species name!")
        return redirect(url_for('question'))
    game = get_game()
    guess_species = game.curr_question.species[choice]
    game.score_question(game.curr_question, guess_species)

    validation = "Correct" if game.curr_question.correct else "Incorrect"


    return render_template('answer.html',
                            question_num = game.question_num,
                            total_questions = game.total_questions,
                            question = game.curr_question,
                            validation = validation)



@app.route('/next', methods=['POST'])
def next():
    game = get_game()

    if game.next_question():
        return redirect(url_for('question'))
    else:
        return redirect(url_for('summary'))

@app.route('/summary', methods=['GET'])
def summary():
    game = get_game()

    return render_template('summary.html',
                           game = game)

@app.template_global(name='zip')
def _zip(*args, **kwargs): #to not overwrite builtin zip in globals
    return __builtins__.zip(*args, **kwargs)

if __name__ == '__main__':
    handler = RotatingFileHandler('planigale.log', maxBytes=10000, backupCount=1)
    # handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.error("It isn't working?")

    app.run()
