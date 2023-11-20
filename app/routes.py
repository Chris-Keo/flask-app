"""
                ---- View Functions ----

This file houses the different URLs that application implements

The functions below are also called handlers. Handlers are also called:
View Functions

Each View Function can be mapped to one or more URLs
"""
from flask import render_template, flash, redirect, url_for# this method converts a template into an HTML page. This invokes Jinja2 template engine. Its shipped with Flask
from app import app # this references the app folder and the app instance inside __init__.py
from app.forms import LoginForm

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
    return render_template('index.html', title = 'Home', user = user, posts = posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm() # Instantiate an object from forms
    if form.validate_on_submit(): # This will evaluate to True if the user clicks the submit button to POST data. 
                                  # Then it will look at forms > LoginForms to validate the data class. If all valid then eval to True.
                                    # So if the user hits triggers the POST method and the data is valid, then it will use flash, which is a method to show user its good
        flash(f'Login requested for user {form.username.data}, remember_me={form.remember_me.data}')
        return redirect('/index') # redirects user to another page
    return render_template('login.html', title = 'Sign In', form = form)

