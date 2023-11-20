"""
This file is needed at the top-level to actually define the Flask application instance
It just needs a single line

from app is the package 
import app is the MEMBER OF the package defined in __init__.py

FYI - can rename the package or the member
"""
from app import app # from app directory import app inside that app directory in a file called __init__.py that has the app instance of Flask
