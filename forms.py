from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, IntegerField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    is_admin = BooleanField('Is Admin')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class TeacherForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=18, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    subjects = SelectMultipleField('Subjects', choices=[])
    titles = SelectMultipleField('Titles', choices=[
        ('bachelor', 'Bachelor'),
        ('master', 'Master'),
        ('phd', 'PhD'),
        ('professor', 'Professor')
    ])

class SubjectForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    schedule = StringField('Schedule', validators=[DataRequired()])
    credits = IntegerField('Credits', validators=[DataRequired(), NumberRange(min=1, max=4)])
    group = StringField('Group', validators=[DataRequired()])
    career = StringField('Career', validators=[DataRequired()])
    total_slots = IntegerField('Total Slots', validators=[DataRequired(), NumberRange(min=1)])
    teacher = SelectField('Teacher', choices=[], coerce=str)

class StudentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    student_code = StringField('Student Code', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])