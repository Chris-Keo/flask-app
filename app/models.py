"""
Schemas
"""
from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import UserMixin # UserMixin gives us access to four methods or generic implementations: is_authenticated, is_active, is_ananymous, get_id
from app import login # importing from app --> __init__.py --> login object


@login.user_loader #register the user loader
def load_user(id):
    return User.query.get(int(id)) # DBs sometime use INT type for the ID


class User(UserMixin, db.Model):
    __tablename__ = 'user_info'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True) # using index makes searches more efficient
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic') # the db.relationship method is used on the one side of the one-to-many relationship. Takes string of Class name not table name


    def __repr__(self):
        return f'<User is {self.username}>'
    
    """
    The set_password and check_password method carry out the secure pw verification
    No need to store original passwords
    """
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
class Post(db.Model):
    __tablename__ = 'post_info'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    body =db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default= datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user_info.id')) # hint: db.ForeignKey looks for the table name not the class name

    def __repr__(self):
        return f'Post {self.body}'

