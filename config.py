import os 

# basedir = os.path.abspath(os.path.dirname(__file__)) ## i think it should be __name__ not __file__
basedir = os.path.abspath(os.path.dirname(__name__))

class Config():
    # configuration settings set as class variables
    SECRET_KEY = os.environ.get('SECRET KEY') or 'you-will-never-guess' # value is an expression with two terms joined by OR operator

    # DATABASE
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False # if set to True, a signal is sent to the app that the DB state has been changed

    # EMAIL
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['chriskeo44@gmail.com']

    # PAGINATION
    POSTS_PER_PAGE = 3
