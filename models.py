from flask_sqlalchemy import SQLAlchemy

from datetime import datetime

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()

def connect_db(app):
    db.app = app
    db.init_app(app)

class User(db.Model):
    '''Users model'''
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.Text, nullable=False, unique=True)
    city = db.Column(db.Text, nullable=False)
    state = db.Column(db.Text, nullable=False)
    lat_lng = db.Column(db.Text)

    pods = db.relationship('Pod', secondary="pod_users", backref='user')
    sub_pods = db.relationship('SubPod', secondary="sub_pod_users", backref='user')
    hobbies = db.relationship('Hobby', secondary='user_hobbies', backref='user')
    pod_messages = db.relationship('PodMessage', backref='pod_user')
    sub_pod_messages = db.relationship('SubPodMessage', backref='sub_pod_user')
    
    @classmethod
    def signup(cls, username, password, first_name, last_name, email, city, state):
        '''Sign up new user'''

        hashed_password = bcrypt.generate_password_hash(password=password).decode('UTF-8')
        new_user = User(
            username=username,
            password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            city=city,
            state=state
        )
        db.session.add(new_user)
        return new_user

    @classmethod
    def authenticate(cls, username,  password):
        '''Check user and password'''
        user = User.query.filter_by(username=username).first()
        if user:
            password = bcrypt.check_password_hash(user.password, password)
            if password:
                return user
        return False

class Pod(db.Model):
    '''Pods/teams model'''
    __tablename__ = 'pods'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(30), unique=True, nullable=False)
    description = db.Column(db.Text)

class SubPod(db.Model):
    __tablename__ = 'sub_pods'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pod_id = db.Column(db.Integer, db.ForeignKey('pods.id'))
    name = db.Column(db.String(30), unique=True, nullable=False)
    description = db.Column(db.Text)
    
class PodUser(db.Model):
    '''Users assigned to Pods'''
    __tablename__ = 'pod_users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pod_id = db.Column(db.Integer, db.ForeignKey('pods.id', ondelete='cascade'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='cascade'))
    owner = db.Column(db.Boolean, default=False)

class SubPodUser(db.Model):
    __tablename__ = 'sub_pod_users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pod_id = db.Column(db.Integer, db.ForeignKey('pods.id', ondelete='cascade'))
    sub_pod_id = db.Column(db.Integer, db.ForeignKey('sub_pods.id', ondelete='cascade'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='cascade'))
    owner = db.Column(db.Boolean, default=False)
    
class PodMessage(db.Model):
    '''User messages'''
    __tablename__ = 'messages_in_pod'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    contents = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='cascade'))
    pod_id = db.Column(db.Integer, db.ForeignKey('pods.id', ondelete='cascade'))

class SubPodMessage(db.Model):
    '''User messages'''
    __tablename__ = 'messages_in_sub_pod'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    contents = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='cascade'))
    pod_id = db.Column(db.Integer, db.ForeignKey('pods.id', ondelete='cascade'))
    sub_pod_id = db.Column(db.Integer, db.ForeignKey('sub_pods.id', ondelete='cascade'))


class Hobby(db.Model):
    '''User hobbies/activities/intrests'''
    __tablename__ = 'hobbies'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(30), nullable=True, unique=True)

class UserHobby(db.Model):
    '''Hobbies to users'''
    __tablename__ = 'user_hobbies'
    hobby_id = db.Column(db.Integer, db.ForeignKey('hobbies.id', ondelete='cascade'), primary_key=True )
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='cascade'), primary_key=True)


class InvitedMembers(db.Model):
    '''Record gets deleted after member joins, so then they could join other pods in the future'''
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    pod_id = db.Column(db.Integer, db.ForeignKey('pods.id'))
    joined = db.Column(db.Boolean, default=False)

class PreviouslyJoined(db.Model):
    '''Keeps the records of people that were invited in the past'''
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    pod_id = db.Column(db.Integer, db.ForeignKey('pods.id'))
    joined = db.Column(db.Boolean, default=False)
