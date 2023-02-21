from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length

class UserForm(FlaskForm):
    '''Create new user form'''
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = Email('Email', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    state = SelectField('State', validators=[DataRequired()])
    
class EditUserForm(FlaskForm):
    '''Edit new user form'''
    username = StringField('Username', validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = Email('Email', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    state = SelectField('State', validators=[DataRequired()])

class UpdatePassword(FlaskForm):
    '''Update/change pasword'''
    curr_password = PasswordField('Current password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    new_password_check = PasswordField('Confirm New Password', validators=[DataRequired()])
    
class PodForm(FlaskForm):
    '''Create new pod/group'''
    pod = StringField('Pod name', validators=[DataRequired()])
    description = TextAreaField('Description')

class MessageForm(FlaskForm):
    '''Message form'''
    title = StringField('Title', validators=[DataRequired()])
    contents = TextAreaField('Contents', validators=[DataRequired()])

class HobbyForm(FlaskForm):
    name = StringField('Hobby/Activity', validators=[DataRequired()])



