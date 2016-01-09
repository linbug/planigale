# planigale

<a href='http://www.recurse.com' title='Made with love at the Recurse Center'><img src='https://cloud.githubusercontent.com/assets/2883345/11325206/336ea5f4-9150-11e5-9e90-d86ad31993d8.png' height='20px'/></a>

Planigale is a game that challenges you to match the picture of the species with its Latin name. 

Available as a [web app](http://planigale.dvndrsn.com/) and on the command line.

Data for Planigale were taken from the [Encyclopedia of Life](http://eol.org/), a repository of all the species known to mankind.

Many cute! Much fun!

------------------------------------------------
##Command line version

Planigale was originally built for the command line. If you want to play, planigale works from [version 1.0](https://github.com/linbug/planigale/releases/tag/48cda76), but the latest version also works on command line.

![alt tag](https://raw.githubusercontent.com/linbug/linbug.github.io/master/_downloads/terminal_planigale.png)

###Dependencies

- Python 3
- Install the following non built-in libraries using pip:

  `pillow` for image processing
  `jsonpickle` for object serialization to json

###Usage

- clone this repo to your computer
- `cd` to the planigale directory in the terminal
- install library dependencies using `pip install -r requirements.txt` (this will also install dependencies for web planiagle as well)
- run `python planigale.py`

------------------------------------------------

##[Web app](http://planigale.dvndrsn.com/)

![alt tag](http://s24.postimg.org/b2cw4uzo5/Screen_Shot_2016_01_08_at_20_30_07.png)

Planigale was a full-stack learning experience. We refactored the command line game into a [Flask](http://flask.pocoo.org/) app, designed the front-end from scratch, hosted it on [Heroku](https://www.heroku.com/) and stored the gameplay state in [Redis](http://redis.io/).

###Dependancies

- Python 3.5.0
- In addition to the libraries used for the command line version above, install the following non-built-in libraries using pip:

    - `flask`
    - `redis`
    - `gunicorn` a WSGI container such as this is required for hosting this app in a production environment.

###Usage

Before running planigale on a local (or remote) host, you must configure two environment variables. Instructions to set environment variables vary based upon your OS and platform.

- `REDIS_URL` must be set to the URL of the Redis instance which is being used for hosting the app. We used a free Redis to Go instance from heroku.
- `PLANIGALE_KEY` must be set to a random value to ensure consistent client side sessions for flask (see (here)[http://flask.pocoo.org/docs/0.10/quickstart/#sessions] for more info).

####Local host

Follow the below instructions to run the planigale web application locally.

- clone this repo to your computer
- `cd` to the planigale directory in terminal
- install library dependencies using `pip install -r requirements.txt`
- Run..
  - `python planigale_flask.py` for flask server in debug mode OR..
  - `gunicorn planigale_flask:app --log-file=-` for gunicorn server
- open a web browser. planigale should be hosted at http://localhost:5000/

####Remote Host

Heroku was used for hosting this flask app. There are some good instructions for getting started with Python on Heroku (here)[https://devcenter.heroku.com/articles/getting-started-with-python-o]. This repository already contains the required files for hosting this on heroku.

- `runtime.txt` is required to specify the Python 3.5.0 runtime for the heroku build process.
- `requirements.txt` specifies the library requirements for the heroku build process.
- `Procfile` specifes the commands and processes which should be run after completing the heroku build process.

If you have the (heroku toolbelt)[https://toolbelt.heroku.com/] installed, you can run the application locally using these settings using the command `heroku local` from the planigale directory.
