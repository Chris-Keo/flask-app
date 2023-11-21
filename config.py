import os 

# basedir = os.path.abspath(os.path.dirname(__file__)) ## i think it should be __name__ not __file__
basedir = os.path.abspath(os.path.dirname(__name__))

class Config():
    SECRET_KEY = os.environ.get('SECRET KEY') or 'you-will-never-guess'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False # if set to True, a signal is sent to the app that the DB state has been changed