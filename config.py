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
    
    # Connection Pooling Configuration for Production
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),  # Number of connections to maintain
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 20)),  # Additional connections beyond pool_size
        'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 30)),  # Seconds to wait for available connection
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 3600)),  # Recycle connections after 1 hour
        'pool_pre_ping': True,  # Verify connections before use
        'echo': os.environ.get('DB_ECHO', 'false').lower() == 'true'  # Log SQL queries (debug only)
    }

    # EMAIL
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['chriskeo44@gmail.com']

    # PAGINATION KNOB
    POSTS_PER_PAGE = 8

    # Languages
    LANGUAGES = ['en','es']
