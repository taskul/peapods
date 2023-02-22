import os
from flask import Flask, render_template, request, redirect, flash, session, g, abort
from sqlalchemy.exc import IntegrityError
from models import db, connect_db, User, Pod, SubPod, Message, PodUser, SubPodUser, PodMessage, SubPodMessage
from forms import UserForm, EditUserForm, UpdatePassword, PodForm, MessageForm, HobbyForm
import click
from dotenv import load_dotenv
from flask.cli import AppGroup
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import ChatGrant
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# This function will read the four configuration variables stored in the .env file 
# and add them to the environment.
account_sid = os.environ.get('ACCOUNT_SID')
auth_token = os.environ.get('AUTH_TOKEN')
api_sid = os.environ.get('SID')
api_secret = os.environ.get('SECRET')
load_dotenv()
CURRENT_USER = "curr_user"

# client = Client(account_sid, auth_token)
# twilio_client = Client()
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = (os.environ.get('DATABASE_URL', 'sqlite:///peapods.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'oh_so_Super_Secr8')

connect_db(app)

chatrooms_cli = AppGroup('chatrooms', help='Manage your chat rooms.')
app.cli.add_command(chatrooms_cli)


@chatrooms_cli.command('list', help='list all chat rooms')
def list():
    conversations = twilio_client.conversations.conversations.list()
    for conversation in conversations:
        print(f'{conversation.friendly_name} ({conversation.sid})')


@chatrooms_cli.command('create', help='create a chat room')
@click.argument('name')
def create(name):
    conversation = None
    for conv in twilio_client.conversations.conversations.list():
        if conv.friendly_name == name:
            conversation = conv
            break
    if conversation is not None:
        print('Chat room already exists')
    else:
        twilio_client.conversations.conversations.create(friendly_name=name)


@chatrooms_cli.command('delete', help='delete a chat room')
@click.argument('name')
def delete(name):
    conversation = None
    for conv in twilio_client.conversations.conversations.list():
        if conv.friendly_name == name:
            conversation = conv
            break
    if conversation is None:
        print('Chat room not found')
    else:
        conversation.delete()    

@app.route('/login', methods=['POST'])
def login():
    payload = request.get_json(force=True)
    username = payload.get('username')
    if not username:
        abort(401)

    # create the user (if it does not exist yet)
    participant_role_sid = None
    for role in twilio_client.conversations.roles.list():
        if role.friendly_name == 'participant':
            participant_role_sid = role.sid
    try:
        twilio_client.conversations.users.create(identity=username,
                                                 role_sid=participant_role_sid)
    except TwilioRestException as exc:
        if exc.status != 409:
            raise

    # add the user to all the conversations
    conversations = twilio_client.conversations.conversations.list()
    for conversation in conversations:
        try:
            conversation.participants.create(identity=username)
        except TwilioRestException as exc:
            if exc.status != 409:
                raise

    # generate an access token
    twilio_account_sid = os.environ.get('ACCOUNT_SID')
    twilio_api_key_sid = os.environ.get('SID')
    twilio_api_key_secret = os.environ.get('SECRET')
    service_sid = conversations[0].chat_service_sid
    token = AccessToken(twilio_account_sid, twilio_api_key_sid,
                        twilio_api_key_secret, identity=username)
    token.add_grant(ChatGrant(service_sid=service_sid))
    
    print(token)
    # send a response
    return {
        'chatrooms': [[conversation.friendly_name, conversation.sid]
                      for conversation in conversations],
        'token': token.to_jwt().decode(),
    }


@app.before_request
def add_user_to_g():
    '''If users is logged in they get added to Flask global variable'''
    if CURRENT_USER in session:
        g.user = User.query.get(session[CURRENT_USER])
    else:
        g.user = None

@app.route('/')
def home():
    form = UserForm()
    return render_template('index.html', form=form)

@app.route('/signup', methods=['GET','POST'])
def signup():
    signup_form = UserForm()

    if signup_form.validate_on_submit():
        username_taken = User.query.filter_by(username=signup_form.username.data).first()
        if username_taken:
            flash('That username is already taken', 'error')

    return render_template('/users/signup.html', signup_form=signup_form)



if __name__=='__main__':
    app.run(debug=True)
