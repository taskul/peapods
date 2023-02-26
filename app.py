import os
import requests
from flask import Flask, render_template, request, redirect, flash, session, g, abort
from sqlalchemy.exc import IntegrityError
from models import db, connect_db, User, Pod, SubPod, Message, PodUser, SubPodUser, PodMessage, SubPodMessage, Hobby, UserHobby
from forms import UserForm, LoginForm, EditUserForm, UpdatePassword, PodForm, MessageForm, HobbyForm
from dotenv import load_dotenv
from flask.cli import AppGroup

load_dotenv()
CURRENT_USER = "curr_user"
OPENWEATHERMAP_API_KEY = os.environ.get('OPENWEATHER_KEY')
TRIPADVISOR_KEY = os.environ.get('TRIPADVISOR_KEY')

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = (os.environ.get('DATABASE_URL', 'sqlite:///peapods.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'oh_so_Super_Secr8')

connect_db(app)
app.app_context().push()

def get_user_lat_lng(user):
    '''returns the string with latitude and longitue based on user location'''
    url = f'http://api.openweathermap.org/geo/1.0/direct?q={user.city},{user.state},US&appid={OPENWEATHERMAP_API_KEY }'
    response = requests.get(url)
    lat = response.json()[0]['lat']
    lng = response.json()[0]['lon']
    return f'{lat},{lng}'

@app.route('/todo/nearby/<category>')
def search_nearby(category):
    '''User to extract location. Category for attractions or restaurants'''
    if CURRENT_USER in session:
        user = User.query.get(session[CURRENT_USER])
        search_nearby_url = "https://api.content.tripadvisor.com/api/v1/location/nearby_search?"
        headers = {"accept": "application/json"}
        params = {'latLong':user.lat_lng, 'key':TRIPADVISOR_KEY, 'category':category, 'language':'en'}
        response = requests.get(search_nearby_url, headers=headers, params=params)
        location_ids = [loc_id['location_id'] for loc_id in response.json()['data']]
        return location_ids

@app.route('/todo/nearby/details/<int:loc_id>', methods=['GET'])
def get_loc_details(loc_id):
    if CURRENT_USER in session:
        details_url = f"https://api.content.tripadvisor.com/api/v1/location/{loc_id}/details?language=en&currency=USD&key={TRIPADVISOR_KEY}"
        headers = {"accept": "application/json"}
        response = requests.get(details_url, headers=headers)
        return response.json()

@app.before_request
def add_user_to_g():
    '''If users is logged in they get added to Flask global variable'''
    if CURRENT_USER in session:
        g.user = User.query.get(session[CURRENT_USER])
    else:
        g.user = None
    print('PRINTING SESSION---------------',session)
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
        # attractions = search_nearby(user=user, category='attractions')
        # print(attractions,'-----------------------')
        # print('---------------------------------------------------------------------')
        return render_template('/users/user_home.html', user=user)
    else:
        return render_template('index.html')

@app.route('/users/signup', methods=['GET','POST'])
def signup():
    form = UserForm()

    if CURRENT_USER in session:
        del session[CURRENT_USER]

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
        lat_long = get_user_lat_lng(user)
        user.lat_lng = lat_long
        db.session.commit()
        return redirect('/pods/create')
    else:
        return render_template('/users/signup.html', form=form)

@app.route('/users/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.authenticate(username=form.username.data, password=form.password.data)
        if user:
            login_user(user)
            return redirect('/')
        else:
            flash('Username or password did not match', 'error')
    return render_template('/users/login.html', form=form)

# ------------------Managing Pods---------------------------
@app.route('/pods/create', methods=['GET', 'POST'])
def create_pod():
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    form = PodForm()
    if form.validate_on_submit:
        try:
            pod = Pod(name=form.name.data, description=form.description.data)
            db.session.add(pod)
            db.session.commit()
            print('G USER-----------------------', g.user, g.user.id)
            pod_relationship = PodUser(
                pod_id=pod.id,
                user_id=g.user.id,
                owner=True
            )
            db.session.add(pod_relationship)
            db.session.commit()
        except IntegrityError:
            flash('Pod with that name already exists', 'error')
            return render_template('/pods/create_pod.html', form=form)
        return redirect('/activities/create')

    else:
        return render_template('/pods/create_pod.html', form=form)


# -----------------------------Managing Hobbies/activities ----------------------

@app.route('/activities/create', methods=['GET', 'POST'])
def activities_create():
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    form = HobbyForm()
    hobbies = [(hobbie, hobbie) for hobbie in Hobby.query.all()]
    form.name.choices = hobbies
    if form.validate_on_submit:
        if form.add_new.data:
            new_hobbie = Hobby(name=form.add_new.data)
            db.session.add(new_hobbie)
            db.session.commit()
            user_hobbie = UserHobby(hobby_id=new_hobbie.id, user_id=g.user.id)
            db.session.add(user_hobbie)
            db.session.commit()
            flash(f'{new_hobbie.name} has been added to your hobbies', 'success')
        elif form.name.data:
            hobby = Hobby.query.filter(Hobby.name==form.name.data)
            user_hobbie = UserHobby(hobby_id=hobby.id, user_id=g.user.id)
            db.session.add(user_hobbie)
            db.session.commit()
            flash(f'{hobby.name} has been added to your hobbies', 'success')
        else:
            flash('The activity already exists', 'error')
            return render_template('/hobbies/add_hobbies.html', form=form, user=g.user)
    return render_template('/hobbies/add_hobbies.html', form=form, user=g.user)


if __name__=='__main__':
    app.run(debug=True)
