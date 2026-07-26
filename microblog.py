"""
This file is needed at the top-level to actually define the Flask application instance
It just needs a single line

from app is the package 
import app is the MEMBER OF the package defined in __init__.py

FYI - can rename the package or the member
"""
from app import app # from app directory import app inside that app directory in a file called __init__.py that has the app instance of Flask. they can be renamed to anything you want, but the convention is to use the same name for both the package and the member of the package. The package is a directory that contains a file called __init__.py, which is executed when the package is imported. The __init__.py file can contain any code you want, but it usually contains the initialization code for the package. In this case, it contains the code to create the Flask application instance.

import sqlalchemy as sa
import sqlalchemy.orm as so

from app import db
from app.models import User, Post

@app.shell_context_processor
def make_shell_context():
    return {'sa':sa, 'so': so, 'db': db, 'User': User, 'Post': Post}
