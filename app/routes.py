"""
                ---- View Functions ----

This file houses the different URLs that application implements

The functions below are also called handlers. Handlers are also called:
View Functions

Each View Function can be mapped to one or more URLs
"""

from app import db
from app.forms import RegistrationForm
from flask import render_template, flash, redirect, url_for, request# render_template method converts a template into an HTML page. This invokes Jinja2 template engine. Its shipped with Flask
from app import app # this references the app folder and the app instance inside __init__.py
from app.forms import LoginForm

from flask_login import current_user, login_user, logout_user, login_required
from app.models import User

from werkzeug.urls import url_parse

# Above each function are URL routes
    # these are decorators, a decorator modifies the functions that follows it
    # a common pattern w/ decorators is to use them to register funcs as callbacks for certain events
@app.route('/')        
@app.route('/index')   
@login_required # this decorator will protect the view if the user is not logged in
def index():

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
    return render_template('index.html', title = 'Home', posts = posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm() # Instantiate an object from forms
    """
    This will evaluate to True if the user clicks the submit button to POST data
    Then it will look at forms > LoginForms to validate the data class. If all valid then eval to True
    So if the user hits triggers the POST method and the data is valid, then it will use flash, which is a method to show user its good
    """
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data): # evaluate to True if user is invalid/none or if the password is incorrect for user
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data) # if it makes to this step. the user is being logged in with login_user()      

        # this variable is for requiring users to login. if they try to access a page and user not logged in. it will send them to login page
            # once they log in they will be redirected back to the page they tried to access before
        next_page = request.args.get('next') # this value will be set to a relative path. The @login_required. See page 51.

        if not next_page or url_parse(next_page).netloc != '': 
            # not next_page means if the login URL does not have a next argument then redirect to index page
            # url_parse(next_page).netloc != '' is to make site secure. if url is a full path then redirect to index page. the next_page value should always be a relative path not absolute path
                # url_parse() is a werkzeug method to help check if a URL is relative or absolute. See page 51
            # if one of the condition is met then set the next_page variable to 'index'
            next_page = url_for('index')

        return redirect(next_page) # redirects user to another page
    return render_template('login.html', title = 'Sign In', form = form)

@app.route('/logout') # this will be in in app/templates/base.html , which is the navigation bar
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET','POST'])
def register():

    # first make sure the user that invokes this function is not ALREADY logged in. If so, redirect
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm() # instantiate form var
    if form.validate_on_submit(): 
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congrats, you are now registered!')
        return redirect(url_for('login'))  # once the user succeeds on registering, it will send them back to login page to proceed
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>') # <dynamic_component> , if that is in the route, it is a dynamic component
@login_required #this page is only accessible to logged in users
def user(username):
    user = User.query.filter_by(username=username).first_or_404() # if there are no results, send back a 404 to the user
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('user.html', user=user, posts=posts)