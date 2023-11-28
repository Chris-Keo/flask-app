from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# This will create the application object as an instance of class Flask
#  __name__ is a predefined variable and points to this file as the starting point to load associated resources
#  __name__ will almost always configure Flask correctly
# the app variable below is instantiated in this file so now it is a member if the app package. It is a package because this folder has the __init__.py file
app = Flask(__name__)
app.config.from_object(Config) # instantiate config variables
db = SQLAlchemy(app) #instantiate a database instance
migrate = Migrate(app, db) # instantiante the migration engine instance and it takes the applications db instance as the second arg

login = LoginManager(app) # this will work mainly with the User Model in app/models.py
login.login_view = 'login' # login is the view function that handles logins

# This import is done here to workaround the issue of circular imports, a common problem with Flask apps
# routes should be another file that exists in the project called routes.py
# models is to define the structure of the database instance, models is a collection of classes called database models
from app import routes, models

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

