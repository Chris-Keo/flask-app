from flask import render_template
from app import app

@app.route('/')        # these are decorators, a decorator modifies the functions that follows it
@app.route('/index')   # a common pattern w/ decorators is to use them to register funcs as callbacks for certain events
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


