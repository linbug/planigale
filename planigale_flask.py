from flask import Flask, render_template, request, redirect
from planigale import Question, Species, Planigale, PlanigaleGame, PlanigaleConsole


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
        question = Question(data)


        if request.method == 'POST':
            entered_answer = request.form["choice"]
            print(entered_answer)

        return render_template('Game.html',
                           question = question)

if __name__ == '__main__':
    data = Planigale.load_species()

    app.run(debug = True)
