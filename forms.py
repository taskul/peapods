from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length, Optional

states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA",
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]

class UserForm(FlaskForm):
    '''Create new user form'''
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[Email()])
    city = StringField('City', validators=[DataRequired()])
    state = SelectField('State', choices=[(st, st) for st in states])

class LoginForm(FlaskForm):
    '''Log in user form'''
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    
class EditUserForm(FlaskForm):
    '''Edit new user form'''
    username = StringField('Username', validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[Email()])
    city = StringField('City', validators=[DataRequired()])
    state = SelectField('State', choices=[(st, st) for st in states])

class UpdatePassword(FlaskForm):
    '''Update/change pasword'''
    curr_password = PasswordField('Current password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    new_password_check = PasswordField('Confirm New Password', validators=[DataRequired()])
    
class PodForm(FlaskForm):
    '''Create new pod/group'''
    name = StringField('Pod name', validators=[DataRequired()])
    description = TextAreaField('Description')

class MessageForm(FlaskForm):
    '''Message form'''
    contents = TextAreaField('Message', validators=[DataRequired(), Length(min=1,max=180)])

# this are both set as optional because we only need one of the fields to process data 
# when creating a new hobby. Create hobby route does checking if the data is valid or not. 
class HobbyForm(FlaskForm):
    name = SelectField('Hobby/Activity', validators=[Optional()])
    add_new = StringField('Add Hobby/Activity', validators=[Optional(), Length(min=0,max=30)])

class InviteMembers(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])



