from flask import Flask, render_template, request, redirect, session, url_for
from planigale import Question, Species, Planigale, PlanigaleGame, PlanigaleConsole
import os

app = Flask(__name__)
app.secret_key =  os.urandom(24)


def get_new_session():
    global curr_session
    curr_session += 1

def get_session_id_game():
    if 'id' not in session:
        session['id'] = get_new_session()
        # forward to question for new game?
    id = session['id']

    if id not in games:
        games[id] = PlanigaleGame(data,total_questions = 5)
        # forward to question for new game?
    game = games[id]

    return id, game

def new_game():
    pass

@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
    id, game = get_session_id_game()

    return render_template('index.html')

@app.route('/question', methods=['GET'])
def question():
    id, game = get_session_id_game()

    return render_template('question.html',
        question_num = game.question_num,
        question = game.curr_question )


@app.route('/answer', methods=['POST'])
def answer():
    id, game = get_session_id_game()
    guess_species = game.curr_question.species[int(request.form["choice"])]
    game.score_question(game.curr_question, guess_species)

    validation = "Correct" if game.curr_question.correct else "Incorrect"


    return render_template('answer.html',
                            question_num = game.question_num,
                            question = game.curr_question,
                            validation = validation)


@app.route('/next', methods=['POST'])
def next():
    id, game = get_session_id_game()

    if game.next_question():
        return redirect(url_for('question'))
    else:
        return redirect(url_for('summary'))

@app.route('/summary', methods=['GET'])
def summary():
    id, game = get_session_id_game()

    return render_template('summary.html',
                           game = game)

@app.template_global(name='zip')
def _zip(*args, **kwargs): #to not overwrite builtin zip in globals
    return __builtins__.zip(*args, **kwargs)

if __name__ == '__main__':

    curr_session = 0

    data = Planigale.load_species()

    games = {}

    app.run(debug = True)
