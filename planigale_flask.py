from flask import Flask
from flask import render_template
from planigale import Question, Species, load_data


app = Flask(__name__)

@app.route('/index')
def index():
        question = Question(data)

        return render_template('Game.html',
                           question = question)


if __name__ == '__main__':
    data = load_data()

    app.run(debug = True)
