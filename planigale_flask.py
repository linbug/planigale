from flask import Flask, render_template, request, redirect, session
from planigale import Question, Species, Planigale, PlanigaleGame, PlanigaleConsole
import os

app = Flask(__name__)
app.secret_key =  os.urandom(24)

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():

        if "current_game" not in session:
            session["current_game"] = PlanigaleGame(data)
            current_question = session["current_game"].questions[0]
        #question = Question(data)

        if request.method == 'POST':
            entered_answer = request.form["choice"]
            print(entered_answer)

        return render_template('Game.html',
                           question = current_question )

if __name__ == '__main__':
    data = Planigale.load_species()

    app.run(debug = True)
