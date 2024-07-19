"""
Flask-WTF uses Python classes to represent web forms.
A form class defines the fields of the forms as class variables.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField # need to import these since Flask_Wtf
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length
from app.models import User

from app import db
import sqlalchemy as sa

# this logs info into Flask user session
class LoginForm(FlaskForm):
    # this will be used in routes.py via import
    username = StringField('Username', validators=[DataRequired()]) # since there is a validators attached, this means flask will generate errors to render in html 
    password =  PasswordField('Password', validators=[DataRequired()]) 
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')
    
    def validate_email(self, email):
        user =User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
        
class EditProfileForm(FlaskForm):
    username =StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About Me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):

        """
        Why use super()
        In the context of the `EditProfileForm` class in Flask, `super()` is used to call the constructor (`__init__` method) of the parent class (`FlaskForm`). 
        Here’s why `super()` is used in this specific case:

        1. **Inheritance**: `EditProfileForm` is inheriting from `FlaskForm`. This means `EditProfileForm` inherits all the attributes and methods of `FlaskForm`.
        2. **Initialization (`__init__` method)**: When you define `__init__` method in a subclass (in this case, `EditProfileForm`), 
                Python does not automatically call the `__init__` method of the parent class (`FlaskForm`). 
                If you want to ensure that the initialization logic of the parent class is executed before adding your own logic, 
                you need to explicitly call `super().__init__(*args, **kwargs)` within your subclass's `__init__` method.
        3. **Passing arguments to the parent class**: In this example, `super().__init__(*args, **kwargs)` ensures that any 
                arguments (`*args` and `**kwargs`) intended for the parent class (`FlaskForm`) are properly passed along. 
                This is crucial because `FlaskForm` might have its own initialization requirements or configurations that need to be handled.
        4. **Accessing parent class methods**: Using `super()` allows you to access and invoke methods from the parent class (`FlaskForm`). 
                In your case, it ensures that the form is properly initialized before you set additional attributes (`self.original_username = original_username`).

        In summary, `super().__init__(*args, **kwargs)` is used in the `EditProfileForm` class to invoke the initialization method of its parent class (`FlaskForm`). 
        This is a standard practice in Python's object-oriented programming to ensure proper inheritance and initialization of classes.

        Why args and Kwargs?
        In Python, `*args` and `**kwargs` are used to pass a variable number of arguments to functions or methods. Here’s why they are commonly used and why they are necessary in the context of the `EditProfileForm` class:

        1. **Variable Number of Arguments**: `*args` and `**kwargs` allow functions and methods to accept any number of positional and keyword arguments, respectively. 
                This flexibility is particularly useful in class constructors (`__init__` methods) where different subclasses might need to accept different sets of parameters.
        2. **Inheritance and Initialization**: When you define a subclass (`EditProfileForm`) that inherits from a parent class (`FlaskForm`), 
                you often need to initialize both the subclass-specific attributes and the attributes of the parent class. `super().__init__(*args, **kwargs)` ensures that 
                any arguments intended for the parent class (`FlaskForm`) are properly passed along. This means that if `FlaskForm`'s constructor expects certain parameters, `args` and `kwargs` allow `EditProfileForm` to 
                handle those parameters correctly without needing to know the specifics of each.
        3. **Forwarding Arguments**: In your specific example, `self.original_username` is an attribute specific to `EditProfileForm`, but `FlaskForm` might also have its own initialization requirements 
                that need to be satisfied. By using `*args` and `**kwargs`, any arguments intended for `FlaskForm` can be forwarded appropriately, ensuring that both `FlaskForm` 
                and `EditProfileForm` are initialized correctly.
        4. **Maintaining Compatibility**: Using `*args` and `**kwargs` makes your code more flexible and compatible with future changes. 
                If the parent class (`FlaskForm`) changes its constructor signature or if subclasses (`EditProfileForm`) need additional parameters, 
                you can adjust the `args` and `kwargs` passed to `super().__init__` without modifying the subclass directly.

        In essence, `args` and `kwargs` are used in the `EditProfileForm` class (and generally in Python) to handle dynamic arguments passed to constructors, 
                ensuring proper initialization of both the subclass and its parent class while maintaining flexibility and compatibility in object-oriented design.
        """
        super().__init__(*args, **kwargs) # need super here to inherit everything from the inherited FlaskForm, so now we can add our own variables
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = db.session.scalar(sa.select(User).where(
                User.username == username.data))
            if user is not None:
                raise ValidationError(f'{user} already exists...Please use a different username.')

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')

class PostForm(FlaskForm):
    post = TextAreaField('Say something', validators=[DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Submit')

