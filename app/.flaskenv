# Use python-dotenv library so we dont have to set environment variables in the terminal every time we want to run the app. 
# Terminals do not persist environment variables across sessions, so we need to set them every time we open a new terminal.
# This file will be automatically loaded by Flask when the app is run. It will set the environment variables for the app. The variables are used to configure the app. The variables are:

FLASK_APP=microblog.py
FLASK_ENV=development
FLASK_DEBUG=1 # 1 to enable debugging and hot reloading