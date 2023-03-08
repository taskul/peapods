import os
import requests
from flask import Flask, render_template, request, redirect, flash, session, g, abort
from sqlalchemy.exc import IntegrityError
from models import db, connect_db, User, Pod, SubPod, PodMessage, SubPodMessage, PodUser, SubPodUser, Hobby, UserHobby, InvitedMembers, PreviouslyJoined
from forms import (UserForm, 
                   EditUserForm, 
                   LoginForm, 
                   EditUserForm, 
                   UpdatePassword, 
                   PodForm, 
                   MessageForm, 
                   HobbyForm, 
                   InviteMembers,
                   InviteExistingMembers)
from dotenv import load_dotenv
from send_email import send_invite

load_dotenv()
CURRENT_USER = "curr_user"
OPENWEATHERMAP_API_KEY = os.environ.get('OPENWEATHER_KEY')
TRIPADVISOR_KEY = os.environ.get('TRIPADVISOR_KEY')

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = (os.environ.get('DATABASE', 'sqlite:///peapods.db'))
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
    print(response)
    lat = response.json()[0]['lat']
    lng = response.json()[0]['lon']
    return f'{lat},{lng}'

def get_user_lat_lng2():
    city = 'Hayfield'
    state = 'MN'
    '''returns the string with latitude and longitue based on user location'''
    url = f'http://api.openweathermap.org/geo/1.0/direct?q={city},{state},US&appid={OPENWEATHERMAP_API_KEY }'
    response = requests.get(url)
    lat = response.json()[0]['lat']
    lng = response.json()[0]['lon']
    return f'{lat},{lng}'

get_user_lat_lng2()

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
        print(response.json())
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
            
def invited_to_pod(email):
    '''check if user has an invitation to a Pod, if yes aissgn them to the Pod'''
    has_invitation = InvitedMembers.query.filter(InvitedMembers.email==email).first()
    if has_invitation:
        # get the Pod id in order to assign member to the Pod
        assigned_pod = has_invitation.pod_id
        # create a record that this person has joined this Pod in the past
        has_joined_in_past = PreviouslyJoined(first_name=has_invitation.first_name,
                                              last_name=has_invitation.last_name,
                                              email=has_invitation.email,
                                              pod_id=has_invitation.pod_id,
                                              joined=True)
        db.session.add(has_joined_in_past)
        db.session.commit()
        # delete record from InvitedMembers, so then that person can join other Pods when they leave
        db.session.delete(has_invitation)
        db.session.commit()
        return assigned_pod
    else:
        return False

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
            sub_pods = user.sub_pods
            # get all people associated with the pod connected to the current user
            team = PodUser.query.filter(PodUser.pod_id==pod.id).all()
            # create a list of user objects that we can itterate over on the front end
            team_members = [User.query.get(member.user_id) for member in team if member.user_id != user.id]
            return render_template('/users/user_dashboard.html',  
                                   pod=pod, sub_pods=sub_pods, 
                                   user=user, pod_member=pod_member, 
                                   team=team_members)
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
                username=form.username.data.lower(), 
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
        # check if user has been invited to join a pod
        assigned_pod = invited_to_pod(user.email)
        if assigned_pod:
            # they have been invited based on their email, add them to the Pod
            user_pod = PodUser(pod_id=assigned_pod, user_id=user.id)
            db.session.add(user_pod)
            db.session.commit()
            return redirect('/')
        else:
            # if they have not been invited, then they can create a new Pod. 
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

# ----------------------------------Managing User---------------------------

@app.route('/users/profile/<int:user_id>')
def user_profile(user_id):
    # check to see if user is logged in an authorized to access resource
    if not g.user:
        flash("Access unauthorized.", "error")
        return redirect("/")
    user, pod, pod_member = is_pod_member()
    user_profile = User.query.get(user_id)
    # prevents logged in users from views members from other pods.
    if user_profile.pods[0].id != pod.id:
        flash("Access unauthorized.", "error")
        return redirect("/")
    current_user_hobbies = user.hobbies
    profile_user_hobbies = user_profile.hobbies
    profile_owner = None
    if user_profile.id == user.id:
        profile_owner = True
    return render_template('/users/user_profile.html', 
                           user_profile=user_profile, 
                           profile_owner=profile_owner,
                           current_user=user, 
                           current_user_hobbies=current_user_hobbies, 
                           profile_user_hobbies=profile_user_hobbies
                           )

@app.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    # check to see if user is logged in an authorized to access resource
    if not g.user:
        flash("Access unauthorized.", "error")
        return redirect("/")
    # if profile user id does not match curretly logged in user
    if user_id != g.user.id:
        flash("Access unauthorized.", "error")
        return redirect("/")
    user, pod, pod_member = is_pod_member()
    form = EditUserForm(obj=user)
    if form.validate_on_submit():
        user = g.user
        user.username=form.username.data
        user.first_name=form.first_name.data
        user.last_name=form.last_name.data
        user.email=form.email.data
        user.city=form.city.data
        user.state=form.state.data
        db.session.commit()
        return redirect(f'/users/profile/{user_id}')
    return render_template('/users/edituser.html', form=form, user=user, pod_member=pod_member)

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

@app.route('/pods/add_members', methods=['GET', 'POST'])
def add_pod_members():
    # returns User object, Pod Object and PodUser object
    user, pod, pod_member = is_pod_member()
    # check to see if user is logged in an authorized to access resource
    # check to see if the user is the owner of the pod
    if not g.user and not pod_member.owner:
        flash("Access unauthorized.", "error")
        return redirect("/")
    form = InviteMembers()
    all_invited = InvitedMembers.query.filter(InvitedMembers.joined.is_(False),InvitedMembers.pod_id==pod.id).all()
    joined = PreviouslyJoined.query.filter(PreviouslyJoined.joined.is_(True),PreviouslyJoined.pod_id==pod.id).all()
    if form.validate_on_submit():
        sender_name = f'{user.first_name} {user.last_name}'
        reciever_name = f'{form.first_name.data}'
        # send an email
        send_invite(reciever_email=form.email.data,
                    sender_name=sender_name, 
                    reciever_name=reciever_name, 
                    pod_name=pod.name)
        # create a record of people who were invited
        invited = InvitedMembers(first_name=form.first_name.data,
                                 last_name=form.last_name.data,
                                 email=form.email.data,
                                 pod_id=pod.id)
        db.session.add(invited)
        db.session.commit()
        return redirect('/pods/add_members')
    return render_template('/pods/add_members.html', form=form, pod_member=pod_member, invited=all_invited, joined=joined)

@app.route('/pods/<int:pod_id>', methods=['GET', 'POST'])
def pod_home(pod_id):
    if not g.user:
        flash("Access unauthorized.", "error")
        return redirect("/")
    # user messages form
    form = MessageForm()
    # returns User object, Pod Object and PodUser object
    user, pod, pod_member = is_pod_member()
    # prevent logged in users from accessing Pods from other teams
    if pod.id != pod_id:
        flash("Access unauthorized.", "error")
        return redirect("/")
    if form.validate_on_submit():
        message = PodMessage(contents=form.contents.data,
                          user_id=user.id,
                          pod_id=pod.id)
        db.session.add(message)
        db.session.commit()
        return redirect(f'/pods/{pod_id}')
    # PodMessage has a backref relationship with User, so we can access user info 
    # on front end with message.pod_user.first_name
    pod_messages = PodMessage.query.filter(PodMessage.pod_id==pod.id).order_by(PodMessage.timestamp.desc()).all()
    return render_template('/pods/pod.html', form=form, pod=pod, pod_member=pod_member, pod_messages=pod_messages)


# delete pod messages
@app.route('/pods/<int:pod_id>/delete/message/<int:msg_id>')
def delete_pod_message(msg_id, pod_id):
    # check to see if user is logged in an authorized to access resource
    if not g.user:
        flash("Access unauthorized.", "error")
        return redirect("/")
    # returns User object, Pod Object and PodUser object
    user, pod, pod_member = is_pod_member()
    message = PodMessage.query.filter(PodMessage.pod_id==pod_id, PodMessage.user_id==user.id, PodMessage.id==msg_id).first()
    if message:
        db.session.delete(message)
        db.session.commit()
        return redirect(f'/pods/{pod_id}')
    else:
        return redirect(f'/pods/{pod_id}')
    
# delete users
@app.route('/pods/<int:pod_id>/delete/user/<int:user_id>')
def delete_pod_user(pod_id, user_id):
    # check to see if user is logged in an authorized to access resource
    if not g.user:
        flash("Access unauthorized.", "error")
        return redirect("/")
    # returns User object, Pod Object and PodUser object
    user, pod, pod_member = is_pod_member()
    if not pod_member.owner:
        flash("Access unauthorized.", "error")
        return redirect(f"/pods/manage")
    user = PodUser.query.filter(PodUser.user_id==user_id).first()
    db.session.delete(user)
    db.session.commit()
    sub_pod_user = SubPodUser.query.filter(SubPodUser.user_id==user_id).all()
    for deleted_user in sub_pod_user:
        db.session.delete(deleted_user)
        db.session.commit()
    delete_user = User.query.get(user_id)
    flash(f"User {delete_user.first_name} has been deleted from {pod.name} Pod", "success")
    return redirect(f"/pods/manage")

# leave pod
@app.route('/pods/<int:pod_id>/leave/user/<int:user_id>')
def leave_pod(pod_id, user_id):
    # check to see if user is logged in an authorized to access resource
    if not g.user:
        flash("Access unauthorized.", "error")
        return redirect("/")
    # returns User object, Pod Object and PodUser object
    user, pod, pod_member = is_pod_member()
    if not pod_member:
        flash("Access unauthorized.", "error")
        return redirect(f"/pods/manage")
    user = PodUser.query.filter(PodUser.user_id==user_id).first()
    db.session.delete(user)
    db.session.commit()
    sub_pod_user = SubPodUser.query.filter(SubPodUser.user_id==user_id).all()
    for deleted_user in sub_pod_user:
        db.session.delete(deleted_user)
        db.session.commit()
    flash(f"You have successfully left {pod.name} Pod", "success")
    return redirect(f"/")
    

# ----------------------------------Managing Sub-Pods---------------------------
@app.route('/sub_pods/create', methods=['GET', 'POST'])
def create_sub_pod():
    # check to see if user is logged in an authorized to access resource
    if not g.user:
        flash("Access unauthorized.", "error")
        return redirect("/")
    # returns User object, Pod Object and PodUser object
    user, pod, pod_member = is_pod_member()
    form = PodForm()
    if form.validate_on_submit():
        if not pod:
            flash('Create a Pod first, before trying to create a Sub-Pod', 'error')
            return redirect('/sub-pods/create')
        try:
            sub_pod = SubPod(pod_id=pod.id, name=form.name.data, description=form.description.data)
            db.session.add(sub_pod)
            db.session.commit()
            sub_pod_relationship = SubPodUser(
                pod_id=pod.id,
                sub_pod_id=sub_pod.id,
                user_id=user.id,
                owner=True
            )
            db.session.add(sub_pod_relationship)
            db.session.commit()
            return redirect('/')
        except IntegrityError:
            flash('Sub-Pod with that name already exists', 'error')
            return redirect('/')
    return render_template('/pods/create_subpod.html', form=form, pod=pod, pod_member=pod_member)

@app.route('/sub_pods/manage')
def manage_sub_pod():
    # returns User object, Pod Object and PodUser object
    user, pod, pod_member = is_pod_member()
    # check to see if user is logged in an authorized to access resource
    # check to see if the user is the owner of the pod
    if not g.user:
        flash("Access unauthorized.", "error")
        return redirect("/")
    sub_pods = user.sub_pods
    sub_pods_owned = None
    if sub_pods:
        is_sub_pod_owner = SubPodUser.query.filter(SubPodUser.pod_id==pod.id, 
                                                 SubPodUser.user_id==user.id, 
                                                 SubPodUser.owner.is_(True)).all()
        sub_pods_owned = [SubPod.query.get(sub_pod.sub_pod_id) for sub_pod in is_sub_pod_owner]
        return render_template('/pods/manage_subpod.html', pod=pod, sub_pods_owned=sub_pods_owned, pod_member=pod_member)
    
    return render_template('/pods/manage_subpod.html', pod=pod, pod_member=pod_member, sub_pods_owned=sub_pods_owned)

@app.route('/sub_pods/edit/<int:sub_pod_id>', methods=['GET', 'POST'])
def edit_sub_pod(sub_pod_id):
    # check to see if user is logged in an authorized to access resource
    if not g.user:
        flash("Access unauthorized.", "error")
        return redirect("/")
    # returns User object, Pod Object and PodUser object
    user, pod, pod_member = is_pod_member()
    owns_sub_pod = SubPodUser.query.filter(SubPodUser.sub_pod_id==sub_pod_id,
                                           SubPodUser.user_id==user.id,
                                           SubPodUser.owner.is_(True)).first()
    sub_pod = SubPod.query.get(sub_pod_id)
    existing_members =  SubPodUser.query.filter(SubPodUser.sub_pod_id==sub_pod_id,
                                        SubPodUser.pod_id==pod.id).all()
    sub_pod_members = [User.query.get(member.user_id) for member in existing_members]
    # no form if user does not own the sub_pod
    form = None
    if owns_sub_pod:
        form = InviteExistingMembers()
        available_members = [ User.query.get(user.user_id) for user in 
                             PodUser.query.filter(PodUser.pod_id==pod.id).all()]
        list_of_names = [(user.id, f'{user.last_name}, {user.first_name}') for user in available_members]
        form.user_id.choices = list_of_names
        if form.validate_on_submit():
            new_member = SubPodUser(pod_id=pod.id,
                                    sub_pod_id=sub_pod_id,
                                    user_id=int(form.user_id.data))
            db.session.add(new_member)
            db.session.commit()
            return redirect(f'/sub_pods/edit/{sub_pod_id}')


    return render_template('/pods/sub_pods_edit.html', form=form, owns_sub_pod=owns_sub_pod, sub_pod=sub_pod,sub_pod_members=sub_pod_members)


@app.route('/sub_pods/<int:sub_pod_id>', methods=['GET', 'POST'])
def sub_pod_home(sub_pod_id):
    # check to see if user is logged in an authorized to access resource
    if not g.user:
        flash("Access unauthorized.", "error")
        return redirect("/")
    # returns User object, Pod Object and PodUser object
    user, pod, pod_member = is_pod_member()
    # check if user is a member of the sub pod
    member_of_sub_pod = SubPodUser.query.filter(SubPodUser.sub_pod_id==sub_pod_id,SubPodUser.user_id==user.id).first()
    if not member_of_sub_pod:
        flash("Access unauthorized.", "error")
        return redirect("/")
    # all messages for current sub pod
    sub_pod_messages = SubPodMessage.query.filter(SubPodMessage.sub_pod_id==sub_pod_id).order_by(SubPodMessage.timestamp.desc()).all()
    # get sub_pod info
    sub_pod = SubPod.query.get(sub_pod_id)
    form = MessageForm()
    if form.validate_on_submit():
        sub_pod_message = SubPodMessage(contents=form.contents.data,
                                        user_id=user.id,
                                        pod_id=pod.id,
                                        sub_pod_id=sub_pod_id)
        db.session.add(sub_pod_message)
        db.session.commit()
        return redirect(f'/sub_pods/{sub_pod_id}')
    return render_template('/pods/sub_pod.html', form=form, 
                           sub_pod=sub_pod, 
                           sub_pod_messages=sub_pod_messages, 
                           user=user, 
                           pod_member=pod_member)

# delete sub pod messages
@app.route('/sub_pods/<int:sub_pod_id>/messages/delete/<int:msg_id>')
def delete_sub_pod_message(msg_id, sub_pod_id):
    # check to see if user is logged in an authorized to access resource
    if not g.user:
        flash("Access unauthorized.", "error")
        return redirect("/")
    # returns User object, Pod Object and PodUser object
    user, pod, pod_member = is_pod_member()
    message = SubPodMessage.query.filter(SubPodMessage.sub_pod_id==sub_pod_id, SubPodMessage.user_id==user.id, SubPodMessage.id==msg_id).first()
    if message:
        db.session.delete(message)
        db.session.commit()
        return redirect(f'/sub_pods/{sub_pod_id}')
    else:
        return redirect(f'/sub_pods/{sub_pod_id}')
    

# leave sub pod
@app.route('/sub_pods/<int:sub_pod_id>/leave/user/<int:user_id>')
def leave_sub_pod(sub_pod_id, user_id):
    # check to see if user is logged in an authorized to access resource
    if not g.user:
        flash("Access unauthorized.", "error")
        return redirect("/")
    # returns User object, Pod Object and PodUser object
    user, pod, pod_member = is_pod_member()
    sub_pod = SubPod.query.get(sub_pod_id)
    if not pod_member:
        flash("Access unauthorized.", "error")
        return redirect(f"/pods/manage")
    sub_pod_user = SubPodUser.query.filter(SubPodUser.user_id==user_id, SubPodUser.sub_pod_id==sub_pod_id).first()
    db.session.delete(sub_pod_user)
    db.session.commit()
    flash(f"You have successfully left {sub_pod.name} Sub-Pod", "success")
    return redirect(f"/")
        

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
