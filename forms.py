from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, IntegerField, FieldList
from wtforms.validators import InputRequired, Length, Optional, Email, EqualTo
from models import Diet


class UserAddForm(FlaskForm):
    """Form for adding users."""

    email = StringField('E-mail', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired(), EqualTo("confirm", message="Passwords don't match"), Length(min=6, message="Password Requirements Not Met")])
    confirm = PasswordField("Retype Password")
    username = StringField('Username', validators=[InputRequired()])



class LoginForm(FlaskForm):
    """Login form."""

    email = StringField('E-mail', validators=[InputRequired(), Email(message="Email not entered")])
    password = PasswordField('Password', validators=[InputRequired("Entry Required"), Length(min=6)])


class RecipeForm(FlaskForm):
    """Form for entering recipe to be analyzed"""
    title = StringField('Title', validators=[InputRequired("Recipe Title Required")])
    servings = IntegerField('Servings', validators=[InputRequired("Servings required")]) 
    ingredients = TextAreaField('Ingredients (Enter valid quantities (lbs, tsp, etc) and use a "," after entering each ingredient.', validators=[InputRequired()])


