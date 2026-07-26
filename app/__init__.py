from flask import Flask, request
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_babel import Babel

import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os

# Add debug prints for environment variables
print("\n=== Environment Variables ===")
print(f"DATABASE_URL: {os.environ.get('DATABASE_URL')}")
print(f"Current working directory: {os.getcwd()}")
print(f"Environment variables available: {list(os.environ.keys())}")
print("===========================\n")

def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])

# This will create the application object as an instance of class Flask
#  __name__ is a predefined variable and points to this file as the starting point to load associated resources, like template files, static files, etc. It is used by Flask to determine the root path of the application so that it can find resource files relative to the location of this file.
#  __name__ will almost always configure Flask correctly
# the app variable below is instantiated in this file so now it is a member if the app package. It is a package because this folder has the __init__.py file
app = Flask(__name__) # <-- this is a flask app instance
app.config.from_object(Config) # instantiate config variables, comes from config.py module located in the top level directory, hence ".config" and use method from_object to call the class Config inside config.py

# Add request logging
@app.before_request
def log_request_info():
    app.logger.info('Request Headers: %s', request.headers)
    app.logger.info('Request Body: %s', request.get_data())
    app.logger.info('Request URL: %s %s', request.method, request.url)

@app.after_request
def log_response_info(response):
    app.logger.info('Response Status: %s', response.status)
    app.logger.info('Response Headers: %s', response.headers)
    return response

db = SQLAlchemy(app) #instantiate a database instance
migrate = Migrate(app, db) # instantiante the migration engine instance and it takes the applications db instance as the second arg
mail = Mail(app)
moment = Moment(app)
babel = Babel(app, locale_selector=get_locale)


login = LoginManager(app) # this will work mainly with the User Model in app/models.py and it expects certain properties and methods to be implemented in it
login.login_view = 'login' # we need to tell Flask-Logins' ....login_view which view function handles the logins. 'login' is the view function in routes.py that handles logins

if not app.debug:
    # email errors
    if app.config['MAIL_SERVER']:
        auth= None
        if app.config['MAIL_SERVER'] or  app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None

        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr = 'no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'], subject='microblog failure',
            credentials=auth, secure=secure
        )
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

    # logging
    if not os.path.exists('logs'):
        os.mkdir('logs') # if a log file does not exist create one
    file_handler = RotatingFileHandler('logs/microblog.log', maxBytes=10240,
                                       backupCount=10) # use rotatingfilehandler to make sure we dont save too many logs that will take up space
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Microblog startup')

# This import is done here to workaround the issue of circular imports, a common problem with Flask apps
# routes should be another file that exists in the project called routes.py.
# Routes are handlers for the different URLs that the application will respond to. They are view functions
# that are decorated with route decorators to specify which URL they handle. you can map one ore more view functions to a single URL, 
#   and you can also map a single view function to multiple URLs. The view function will be called when the URL is accessed, and it will return a response to the client.
# models is to define the structure of the database instance, models is a collection of classes called database models
from app import routes, models, errors



if __name__ == '__main__':
    """
    pip install python-dotenv
    then add a .env file with contents

    FLASK_APP = microblog.py
    FLASK_ENV= development
    FLASK_DEBUG=1

    when running app, use this command to get hot reload:
        flask --debug run
    """
    app.run(host='0.0.0.0',debug=True)

