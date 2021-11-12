import os

from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from forms import UserAddForm, LoginForm, RecipeForm

# from forms import UserAddForm, LoginForm, MessageForm, UserEditForm

from models import db, connect_db, User, Diet, UserDiet
from secrets import apiKey

CURR_USER_KEY = "curr_user"

app = Flask(__name__)



# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///nutree'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "i'll never tell")
toolbar = DebugToolbarExtension(app)

BASE_URL = "https://api.spoonacular.com/"

connect_db(app)


##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.email


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/', methods=["GET", "POST"])
def signup():
    """username user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                email=form.email.data,
                password=form.password.data,
                username = form.username.data,
            )
            db.session.commit()

        except IntegrityError:
            flash("e-mail already exists in our database. If password has been forgotten, please request a password reset", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect(f"/home/{g.user.email}")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """username user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.email.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect(f"/home/{g.user.email}")

        flash("Invalid email/password combination. Try Again", 'danger')

    return render_template('users/signup.html', form=form)


@app.route('/logout')
def logout():
    """username logout of user."""
    do_logout()
    flash("You have been successfully logged out")

    return redirect("/")


##############################################################################
# General user routes:


@app.route('/home/<string:user_email>', methods=['GET'])
def user_home(user_email):
    """Show user homepage."""

    form = RecipeForm()

    user = User.query.get_or_404(user_email)

    # Getting user's diets from database
    chosen_diets = (Diet
                .query
                .filter(UserDiet.user_email == user_email)
                .all())

    available_diets = Diet.query.all()

    


    return render_template('users/signed-in-home.html', user=user, chosen_diets=chosen_diets, avaliable=available_diets, form=form)


@app.route('/home/<string:user_email>', methods=['POST'])
def recipe(user_email):
    """Receives text from the recipe field in the HTML file"""

    recipe = dict()
    recipe_list = list(recipe)
    form = RecipeForm(request.form)

    if form.validate_on_submit() and request.method == "POST":
        
        try:
            recipe = dict()
            recipe_list = list(recipe)
            
            title = form.title.data 
            servings= form.servings.data
            ingredients= form.ingredients.data
            instructions= form.instructions.data

            recipe["title"] = title
            recipe["servings"] = servings
            recipe["ingredients"] = ingredients
            recipe["instuctions"] = instructions

            print(recipe)
            
        except IntegrityError:
            flash("e-mail already exists in our database. If password has been forgotten, please request a password reset", 'danger')
            print("satan took over the computer")
            return redirect(f'/home/{user_email}')



    print("COULD NOT VALIDATE", form.validate_on_submit(), request.method)
    return redirect(f'/home/{user_email}')

        









            

        



    












##############################################################################

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
