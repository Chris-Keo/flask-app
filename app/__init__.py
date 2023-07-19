from flask import Flask

# This will create the application object as an instance of class Flask
#  __name__ is a predefined variable and points to this file as the starting point to load associated resources
#  __name__ will almost always configure Flask correctly
app = Flask(__name__)

from app import routes

if __name__ == '__main__':
    app.run(debug=True)