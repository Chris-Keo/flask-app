"""
Schemas
"""
from datetime import datetime, timezone
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from dataclasses import dataclass

from flask_login import UserMixin # UserMixin gives us access to four methods or generic implementations: is_authenticated, is_active, is_ananymous, get_id
from app import login # importing from app --> __init__.py --> login object
import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import Optional
from hashlib import md5


# this is used to load the user in the app so the user can navigate through the app and be remembered. flask-login retrieves id of the user and loads it
@login.user_loader # a flask_login decorator used to register the user loader
def load_user(id):
    return User.query.get(int(id)) # DBs sometime use INT type for the ID

# need to create this "associated table", which is for a relationship where instances of a class is linked to other instances of the same class, called self referential relationship
    # the followers object represents a sql table. and as you can see this table consists of two FKs and both are PKs, this is called compound primary key
followers = sa.Table(
    'followers',
    db.metadata,
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('User.id'),primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('User.id'),primary_key=True),
)


class User(UserMixin, db.Model):
    __tablename__ = 'User'
    __table_args__ = {'extend_existing': True}
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True,
                                         unique=True) # using index makes searches more efficient
    email: so.Mapped[str] =  so.mapped_column(sa.String(120), index=True,
                                              unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    posts: so.WriteOnlyMapped['Post'] = so.relationship('Post', back_populates='author') # the db.relationship method is used on the one side of the one-to-many relationship. Takes string of Class name not table name
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen:so.Mapped[Optional[datetime]] =so.mapped_column(default=lambda: datetime.now(timezone.utc))

    following: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates='followers'
    )

    followers: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.followed_id ==  id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates='following'
    )

    def follow(self, user):
        if not self.is_following(user):
            self.following.add(user)
    
    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def is_following(self, user):
        query = self.following.select().where(User.id == user.id)
        return db.session.scalar(query) is not None
    
    def followers_count(self):
        query = sa.select(sa.func.count()).select_from(self.followers.select().subquery()) # need to add subquery() because it is the inner query of the larger query
        return db.session.scalar(query)

    def following_count(self):
        query = sa.select(sa.func.count()).select_from(self.following.select().subquery()) # need to add subquery() because it is the inner query of the larger query
        return db.session.scalar(query)
    
    def following_posts(self):
        # will show the user and the user followers posts
        Author = so.aliased(User)
        Follower = so.aliased(User)

        return (sa.select(Post)
                .join(Post.author.of_type(Author))
                .join(Author.followers.of_type(Follower), isouter=True) # isouter=True makes this a left outer join, which preserves items on left side that have no match to right
                .where(sa.or_(     # using a compound filter
                    Follower.id == self.id, # gets posts that have a user as the follower
                    Author.id == self.id))  # gets posts that have a user as the author
                .group_by(Post)
                .order_by(Post.timestamp.desc())
                )

    def __repr__(self):
        return f'<User {self.username}>'
    
    """
    The set_password and check_password method carry out the secure pw verification
    No need to store original passwords
    """
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'
    
class Post(db.Model):
    __tablename__ = 'Post'
    __table_args__ = {'extend_existing': True}
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc)) # used index True here for retrieving posts in chronological order
    user_id: so.Mapped[str] = so.mapped_column(sa.ForeignKey(User.id),
                                              index=True) # hint: db.ForeignKey looks for the table name not the class name
    author: so.Mapped[User] = so.relationship('User', back_populates='posts')
    
    def __repr__(self):
        return f'Post {self.body}'


