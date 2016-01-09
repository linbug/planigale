# planigale

<a href='http://www.recurse.com' title='Made with love at the Recurse Center'><img src='https://cloud.githubusercontent.com/assets/2883345/11325206/336ea5f4-9150-11e5-9e90-d86ad31993d8.png' height='20px'/></a>

Planigale is a game that challenges you to match the picture of the species with its Latin name. 

Available as a [web app](http://planigale.dvndrsn.com/) and on the command line.

Data for Planigale were taken from the [Encyclopedia of Life](http://eol.org/), a repository of all the species known to mankind.

Many cute! Much fun!

------------------------------------------------
##Command line version

Planigale was originally built for the command line. If you want to play, you are better off with [version 1.0](https://github.com/linbug/planigale/releases/tag/48cda76).

![alt tag](https://raw.githubusercontent.com/linbug/linbug.github.io/master/_downloads/terminal_planigale.png)

###Dependencies

- Python 3
- the following (non built-in) library:

  `pillow` (install using pip)

##Usage

- clone this repo to your computer
- `cd` to the planigale directory in the terminal and run `python planigale.py`

------------------------------------------------

##[Web app](http://planigale.dvndrsn.com/)

![alt tag](http://s24.postimg.org/b2cw4uzo5/Screen_Shot_2016_01_08_at_20_30_07.png)

Planigale was a full-stack learning experience. We refactored the command line game into a [Flask](http://flask.pocoo.org/) app, designed the front-end from scratch, hosted it on [Heroku](https://www.heroku.com/) and stored the gameplay state in [Redis](http://redis.io/). 

