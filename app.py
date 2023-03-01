import os
import requests
from flask import Flask, render_template, request, redirect, flash, session, g, abort
from sqlalchemy.exc import IntegrityError
from models import db, connect_db, User, Pod, SubPod, Message, PodUser, SubPodUser, PodMessage, SubPodMessage, Hobby, UserHobby
from forms import UserForm, LoginForm, EditUserForm, UpdatePassword, PodForm, MessageForm, HobbyForm, InviteMembers
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

# ---------------------------------API calls to OPENWEATHERMAP-------------------------------
def get_user_lat_lng(user):
    '''returns the string with latitude and longitue based on user location'''
    url = f'http://api.openweathermap.org/geo/1.0/direct?q={user.city},{user.state},US&appid={OPENWEATHERMAP_API_KEY }'
    response = requests.get(url)
    lat = response.json()[0]['lat']
    lng = response.json()[0]['lon']
    return f'{lat},{lng}'

# ---------------------------------API calls to TRIP ADVISOR-------------------------------
@app.route('/todo/nearby/<category>')
def search_nearby(category):
    if not g.user:
        flash("Access unauthorized.", "error")
        return redirect("/")
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
    if not g.user:
        flash("Access unauthorized.", "error")
        return redirect("/")
    if CURRENT_USER in session:
        details_url = f"https://api.content.tripadvisor.com/api/v1/location/{loc_id}/details?language=en&currency=USD&key={TRIPADVISOR_KEY}"
        headers = {"accept": "application/json"}
        response = requests.get(details_url, headers=headers)
        return response.json()
    
# ----------------------------------HELPER FUNCTIONS---Check if user is a member--------------------
def is_pod_member():
    '''check to see if the current user is the pod member,
        returned User object, Pod object, and PodUser object that allows us to check if user is the owner of the pod
    '''
    if g.user:
        #get the user
        user = User.query.get(int(session[CURRENT_USER]))
        # check to see if the user belongs to any pods
        empty_tupple = (None,None,None)
        if user:
            main_pod = user.pods
            if main_pod:
                main_pod = user.pods[0]
                pod_member = PodUser.query.filter(PodUser.pod_id==main_pod.id, PodUser.user_id==user.id).first()
                if pod_member:
                    return user, main_pod, pod_member
                else:
                    return empty_tupple
            else:
                return empty_tupple

# --------------------------------------404 page--------------------------------------------


@app.errorhandler(404)
def serve_404(e):
    """Render 404 page"""
    return render_template("404_page.html"), 404
    
# --------------------------------------Check if user is logged in ------------------------------------
@app.before_request
def add_user_to_g():
    '''If users is logged in they get added to Flask global variable'''
    if CURRENT_USER in session:
        g.user = User.query.get(session[CURRENT_USER])
    else:
        g.user = None

# --------------------------------------User session helper functions ----------------------------------
def login_user(user):
    session[CURRENT_USER] = user.id

def logout_user():
    if CURRENT_USER in session:
        del session[CURRENT_USER]

# --------------------------------------Routes --------------------------------------
@app.route('/')
def home():
    # check to see if the user is logged in
    if g.user:
        # returns User object, Pod Object and PodUser object
        user, pod, pod_member = is_pod_member()
        if pod_member:
            # get all people associated with the pod connected to the current user
            team = PodUser.query.filter(PodUser.pod_id==pod.id).all()
            # create a list of user objects that we can itterate over on the front end
            team_members = [User.query.get(member.user_id) for member in team]
            return render_template('/users/user_dashboard.html',  pod=pod, user=user, pod_member=pod_member, team=team_members)
        else:
            return render_template('/users/user_menu.html')
    else:
        return render_template('index.html')
    
@app.route('/users/signup', methods=['GET','POST'])
def signup():
    form = UserForm()
    # if user is logged in, log them out
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
            flash('Username is already taken', 'error')
            return redirect('/users/signup')

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

@app.route('/users/logout')
def logout():
    '''Handle logout'''
    logout_user()
    flash("You have been logged out.", "success")
    return redirect('/')

# ----------------------------------Managing Pods---------------------------

@app.route('/pods/create', methods=['GET', 'POST'])
def create_pod():
    # check to see if user is logged in an authorized to access resource
    if not g.user:
        flash("Access unauthorized.", "error")
        return redirect("/")
    form = PodForm()
    # returns User object, Pod Object and PodUser object
    user, pod, pod_member = is_pod_member()
    if form.validate_on_submit():
        if pod:
            flash(f'You are already part of the {{pod.name}}', 'error')
        try:
            new_pod = Pod(name=form.name.data, description=form.description.data)
            db.session.add(new_pod)
            db.session.commit()
            pod_relationship = PodUser(
                pod_id=new_pod.id,
                user_id=g.user.id,
                owner=True
            )
            db.session.add(pod_relationship)
            db.session.commit()
            return redirect('/hobbies/create')
        except IntegrityError:
            flash('Pod with that name already exists', 'error')
            return redirect('/pods/create')
    return render_template('/pods/create_pod.html', form=form, pod=pod, pod_member=pod_member)

@app.route('/pods/manage')
def manage_pod():
    # returns User object, Pod Object and PodUser object
    user, pod, pod_member = is_pod_member()
    # check to see if user is logged in an authorized to access resource
    # check to see if the user is the owner of the pod
    if not g.user and not pod_member.owner:
        flash("Access unauthorized.", "error")
        return redirect("/")
    pod_team_members = PodUser.query.filter(PodUser.pod_id==pod_member.pod_id).all()
    team_members = [User.query.get(member.user_id) for member in pod_team_members]
    return render_template('/pods/manage_pod.html', pod=pod, pod_member=pod_member, members=team_members)

@app.route('/pods/add_members')
def add_pod_members():
    # returns User object, Pod Object and PodUser object
    user, pod, pod_member = is_pod_member()
    # check to see if user is logged in an authorized to access resource
    # check to see if the user is the owner of the pod
    if not g.user and not pod_member.owner:
        flash("Access unauthorized.", "error")
        return redirect("/")
    form = InviteMembers()
    if form.validate_on_submit():
        print('Something will happen')
    return render_template('/pods/add_members.html', form=form, pod_member=pod_member)

@app.route('/pods/home/<pod_id>')
def pod_home(pod_id):
    if not g.user:
        flash("Access unauthorized.", "error")
        return redirect("/")
    # user messages form
    form = MessageForm()
    # returns User object, Pod Object and PodUser object
    user, pod, pod_member = is_pod_member()
    if form.validate_on_submit():
        message = Message(title=form.title.data,
                          contents=form.contents.data,
                          user_id=user.id)
        db.session.add(message)
        db.session.commit()
        pod_message = PodMessage(pod_id=pod.id, message_id=message.id)
        db.session.add(pod_message)
        db.session.commit()
        return redirect(f'/pods/home/{pod.id}')
    pod_messages = pod.messages
    return render_template('/pods/pod.html', form=form, pod_messages=pod_messages)


# ----------------------------------Managing Sub-Pods---------------------------
@app.route('/sub-pods/create', methods=['GET', 'POST'])
def create_sub_pod():
    # check to see if user is logged in an authorized to access resource
    if not g.user:
        flash("Access unauthorized.", "error")
        return redirect("/")
    user = User.query.get(int(session[CURRENT_USER]))
    main_pod = user.pods
    form = PodForm()
    if form.validate_on_submit():
        try:
            pod = SubPod(name=form.name.data, description=form.description.data)
            db.session.add(pod)
            db.session.commit()
            pod_relationship = PodUser(
                pod_id=pod.id,
                user_id=g.user.id,
                owner=True
            )
            db.session.add(pod_relationship)
            db.session.commit()
        except IntegrityError:
            flash('Sub-Pod with that name already exists', 'error')
            return redirect('/sub-pods/create')
    return render_template('/pods/create_subpod.html', form=form, pod=main_pod)

# -----------------------------Managing Hobbies/activities ----------------------

@app.route('/hobbies/create', methods=['GET', 'POST'])
def activities_create():
    # check to see if user is logged in an authorized to access resource
    if not g.user:
        flash("Access unauthorized.", "error")
        return redirect("/")
    user = User.query.get_or_404(session[CURRENT_USER])
    form = HobbyForm()
    hobbies = [(hobbie.name, hobbie.name) for hobbie in Hobby.query.all()]
    form.name.choices = hobbies
    if form.validate_on_submit():
        existing_hobbies = [hobby.name for hobby in user.hobbies]
        if form.add_new.data:
            if form.name.data != form.add_new.data:
                try:
                    hobby = Hobby(name=form.add_new.data.lower())
                    db.session.add(hobby)
                    db.session.commit()
                    user_hobbie = UserHobby(hobby_id=hobby.id, user_id=user.id)
                    db.session.add(user_hobbie)
                    db.session.commit()
                    form.add_new.data = ''
                    flash(f'{hobby.name} has been added to your hobbies', 'success')
                except IntegrityError:
                    flash('The activity already exists', 'error')
                    return redirect('/hobbies/create')
        elif form.name.data and (form.name.data not in existing_hobbies):
            hobby = Hobby.query.filter(Hobby.name==form.name.data).first()
            user_hobbie = UserHobby(hobby_id=hobby.id, user_id=user.id)
            db.session.add(user_hobbie)
            db.session.commit()
            flash(f'{hobby.name} has been added to your hobbies', 'success')
            return redirect('/hobbies/create')
        else:
            flash('That activity already exists in a dropdown list', 'error')
            form.add_new.data = ''

    return render_template('/hobbies/add_hobbies.html', form=form, hobbies=user.hobbies)


if __name__=='__main__':
    app.run(debug=True)
