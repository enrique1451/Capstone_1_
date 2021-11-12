from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, IntegerField, FieldList
from wtforms.validators import DataRequired, Length, Optional, Email



class UserAddForm(FlaskForm):
    """Form for adding users."""

    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])
    username = StringField('Username', validators=[DataRequired()])

class LoginForm(FlaskForm):
    """Login form."""

    email = StringField('email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])


class RecipeForm(FlaskForm):
    """Form for entering recipe to be analyzed"""
    title = StringField('Title', validators=[DataRequired()])
    servings = IntegerField('Servings', validators=[DataRequired()]) 
    ingredients = TextAreaField('Ingredients', validators=[DataRequired()])
    instructions = TextAreaField('Instructions', validators=[Optional(strip_whitespace=True)])