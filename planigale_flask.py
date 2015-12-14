from flask import Flask, flash, render_template, request, redirect, session, url_for
from planigale import Question, Species, Planigale, PlanigaleGame, PlanigaleConsole
import os

app = Flask(__name__)
app.secret_key =  os.urandom(24)


def get_new_session():
    global curr_session
    curr_session += 1

def get_session():
    if 'id' not in session:
        session['id'] = get_new_session()
    return session['id']



def get_session_id_game():
    id =get_session()
    if id not in games:
        games[id] = PlanigaleGame(data, total_questions, hints)
        # forward to question for new game?
    game = games[id]
    else:
        redirect(url_for('index'))



    return id, game

def new_game(total_questions,hints):
    game = PlanigaleGame(data, total_questions, hints)



    return game

@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():



    return render_template('index.html')
    if request.method == 'POST':
        try:

            total_questions = int(request.form["num_questions"])

            difficulty_dict = {
            "easy":total_questions,
            "medium": int(total_questions/2),
            "hard": 0
            }

            num_hints = difficulty_dict[request.form["difficulty"]]
            id, game = get_session_id_game(total_questions, num_hints)
        except(Exception):
            id, game = get_session_id_game(3,1)

# @app.route('/newgame', methods = ['POST, GET'])
# def newgame():
#     if request.method == 'POST':
#         try:

#             total_questions = int(request.form["num_questions"])

#             difficulty_dict = {
#             "easy":total_questions,
#             "medium": int(total_questions/2),
#             "hard": 0
#             }

#             num_hints = difficulty_dict[request.form["difficulty"]]
#             id, game = get_session_id_game(total_questions, num_hints)
#         except(Exception):
#             id, game = get_session_id_game(3,1)

        # print("STILL " + str(num_hints) + "and" + str(total_questions) )

        # try:
        #     print("PASSING IN STUFF")
        #     id, game = get_session_id_game(total_questions, num_hints)
        #     print(str(game.num_hints) + " HINTS")
        # except:
        #     id, game = get_session_id_game()




@app.route('/question', methods=['POST','GET'])
def question():

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
    id, game = get_session_id_game()
    guess_species = game.curr_question.species[int(request.form["choice"])]
    game.score_question(game.curr_question, guess_species)

    validation_dict = {True: "Correct!", False: "Incorrect!"}

    return render_template('answer.html',
                            question_num = game.question_num,
                            question = game.curr_question,
                            validation = validation_dict[game.curr_question.correct])



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

if __name__ == '__main__':

    curr_session = 0

    data = Planigale.load_species()

    games = {}

    app.run(debug = True)
