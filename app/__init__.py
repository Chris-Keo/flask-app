from flask import Flask

# This will create the application object as an instance of class Flask
#  __name__ is a predefined variable and points to this file as the starting point to load associated resources
#  __name__ will almost always configure Flask correctly
# the app variable below is instantiated in this file so now it is a member if the app package. It is a package because this folder has the __init__.py file
app = Flask(__name__)

# This import is done here to workaround the issue of circular imports, a common problem with Flask apps
# routes should be another file that exists in the project called routes.py
from app import routes

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

