"""
                ---- View Functions ----

This file houses the different URLs that application implements

The functions below are also called handlers. Handlers are also called:
View Functions

Each View Function can be mapped to one or more URLs
"""
from flask import render_template # this method converts a template into an HTML page. This invokes Jinja2 template engine. Its shipped with Flask
from app import app # this references the app folder and the app instance inside __init__.py

# Above each function are URL routes
    # these are decorators, a decorator modifies the functions that follows it
    # a common pattern w/ decorators is to use them to register funcs as callbacks for certain events
@app.route('/')        
@app.route('/index')   
def index():
    user = {'username': 'Harry'}
    posts = [
        {
        'author':{'username':'John'},
        'body': 'Beatiful day in Portland!'
        },
        {
        'author':{'username':'Susan'},
        'body': 'Gran Turismo is an underdog movie. Recommmend!'
        }   
        ]
    return render_template('index.html', title='Home', user=user, posts=posts)


