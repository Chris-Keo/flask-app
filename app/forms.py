"""
Flask-WTF uses Python classes to represent web forms.
A form class defines the fields of the forms as class variables.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()]) # since there is a validators attached, this means flask will generate errors to render in html 
    password =  PasswordField('Password', validators=[DataRequired()]) 
    remember_me = BooleanField('Remember Me')
    submit =SubmitField('Sign In')