from flask import Flask, flash, render_template, request, redirect, session, url_for
from planigale import Question, Species, Planigale, PlanigaleGame, PlanigaleConsole
import os

app = Flask(__name__)
app.secret_key =  os.urandom(24)


def get_new_session():
    global curr_session
    curr_session += 1


def get_session_id():
    if 'id' not in session:
        session['id'] = get_new_session()
    return session['id']


def get_game():
    id = get_session_id()

    if id not in games:
        games[id] = PlanigaleGame(data)
        # forward to question for new game?
    game = games[id]

    return game


@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/newgame', methods = ['POST'])
def newgame():
    try:
        id = get_session_id()

        total_questions = int(request.form["num_questions"])

        difficulty_dict = {
            "easy":total_questions,
            "medium": int(total_questions/2),
            "hard": 0
        }

        num_hints = difficulty_dict[request.form["difficulty"]]

        games[id] = PlanigaleGame(data, total_questions, num_hints)

        return redirect(url_for('question'))
    except(Exception):
        flash("Error while creating game. Please retry.")
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

    curr_session = 0

    data = Planigale.load_species()

    games = {}

    app.run(debug = True)
