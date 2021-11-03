import os

from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

# from forms import UserAddForm, LoginForm, MessageForm, UserEditForm
from models import db, connect_db, User, Diet, UserDiet

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

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
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
            return render_template('users/index.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/index.html', form=form)


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
            return redirect("/")

        flash("Invalid email/password combination. Try Again", 'danger')

    return render_template('users/index.html', form=form)


@app.route('/logout')
def logout():
    """username logout of user."""
    do_logout()
    flash("You have been successfully logged out")

    return redirect("/")


##############################################################################
# General user routes:


@app.route('/users/<int:user_email>')
def users_show(user_email):
    """Show user profile."""

    user = User.query.get_or_404(user_email)

    # Getting user's diets from database
    diets = (Diets
                .query
                .filter(Diet.user_email == user_email)
                .limit(100)
                .all())


    return render_template('users/show.html', user=user)



@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")


@app.route('/')
def homepage():
    """Show homepage:

    - anon users: just login or signup options
    - logged in: homepage for particular user
    """

    if g.user:

        # cur_user_is_following_ids = [fol.id for fol in g.user.following] + [g.user.id]

            
        messages = (Message
                    .query
                    .filter(Message.user_id.in_(cur_user_is_following_ids))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())

        print(messages)


        
          

        

        return render_template('home.html', messages=messages)

    else:
        return render_template('home-anon.html')









##############################################################################

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
