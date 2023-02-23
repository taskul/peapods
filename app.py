import os
from flask import Flask, render_template, request, redirect, flash, session, g, abort
from sqlalchemy.exc import IntegrityError
from models import db, connect_db, User, Pod, SubPod, Message, PodUser, SubPodUser, PodMessage, SubPodMessage
from forms import UserForm, LoginForm, EditUserForm, UpdatePassword, PodForm, MessageForm, HobbyForm
from dotenv import load_dotenv
from flask.cli import AppGroup

load_dotenv()
CURRENT_USER = "curr_user"

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = (os.environ.get('DATABASE_URL', 'sqlite:///peapods.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'oh_so_Super_Secr8')

connect_db(app)
app.app_context().push()

@app.before_request
def add_user_to_g():
    '''If users is logged in they get added to Flask global variable'''
    if CURRENT_USER in session:
        g.user = User.query.get(session[CURRENT_USER])
    else:
        g.user = None
    print(session)
    print('-----------------------')
    if CURRENT_USER in session:
        print(session[CURRENT_USER])
    print('-----------------------')

# User session helper functions ----------------------------------
def login_user(user):
    session[CURRENT_USER] = user.id

def logout_user(user):
    if CURRENT_USER in session:
        del session[CURRENT_USER]

# Routes --------------------------------------------------------------
@app.route('/')
def home():
    if CURRENT_USER in session:
        user = User.query.get_or_404(int(session[CURRENT_USER]))
        if not user.pods:
            form = PodForm()
            if form.validate_on_submit:
                try:
                    new_pod = Pod(name=form.name.data, description=form.description.data)
                    db.session.add(new_pod)
                    db.session.commit()
                except IntegrityError:
                    flash('Pod name already exists')
                    return render_template('/pods/initial_pod_setup.html', user=user)
                return redirect('/users/invite_team.html')

            return render_template('/pods/initial_pod_setup.html', user=user)
        else:
            return render_template('/users/user_home.html', user=user)
    else:
        return render_template('index.html')

@app.route('/signup', methods=['GET','POST'])
def signup():
    form = UserForm()

    if CURRENT_USER in session:
        return redirect('/')
    if form.validate_on_submit():
        try: 
            user = User.signup(
                username=form.username.data, 
                password=form.password.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data,
                city=form.city.data,
                state=form.state.data
            )
            db.session.commit()
        except IntegrityError:
            flash('Username is already taken', 'danger')
            return render_template('/users/signup.html', form=form)

        login_user(user)
        return redirect('/')
    else:
        return render_template('/users/signup.html', form=form)

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.authenticate(username=form.username.data, password=form.password.data)
        if user:
            login_user(user)
            return render_template('/pods/initial_pod_setup.html', user=user)
        else:
            flash('Username or password did not match', 'error')
    return render_template('/users/login.html', form=form)


if __name__=='__main__':
    app.run(debug=True)
