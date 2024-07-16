from flask import render_template
from app import app, db

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404 # the second return value of 404 takes over the default second return value of 200

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback() # if the error hits then rollback to clean the session slate
    return render_template('500.html'), 500 # the second return value of 404 takes over the default second return value of 200