import os, json

from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from forms import UserAddForm, LoginForm, RecipeForm


from models import db, connect_db, User, Diet, UserDiet
from secrets import apiKey

CURR_USER_KEY = "user_id"

app = Flask(__name__)


# 1 lb spaghetti,
# 3.5 oz pancetta,
# 2 Tbsps olive oil,
# 1  egg,
# 0.5 cup parmesan cheese



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


@app.route('/')
def index():
    if g.user:
        return redirect(f'/users/{g.user}')
    return redirect('/login')



@app.route('/signup', methods=["GET", "POST"])
def signup():

    """username user signup.
    Create new user and add to DB. Redirect to home page.
    If form not valid, present form.
    If the there already is a user with that username: flash message
    and re-present form.
    """
    form = UserAddForm()
    # Grabs diets from Nutree Database and render them dynamically in the Jinja template
    # def diets_in_list():
        
    #     [(d.id, d.name)for d in Diet.query.all()]
    #     diet_list.append(d)
    #     print(diet_list)
    
        

    if form.validate_on_submit() and request.method == "POST":
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
        return redirect(f"/users/{user.id}")

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
            return redirect(f"/users/{user.id}")

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


@app.route('/users/<int:user_id>', methods=['GET'])
def user_home(user_id):
    """Show user homepage."""
    if not g.user:
        flash("Session Expired. Log In to your Account Again", "danger")
        return redirect("/login")

    form = RecipeForm()
    user = User.query.get_or_404(user_id)

    # Getting user's diets from database
    chosen_diets = (Diet
                .query
                .filter(UserDiet.user_id == user_id)
                .all())

    available_diets = Diet.query.all()

    return render_template('users/user_home.html', user=user, chosen_diets=chosen_diets, available_diets=available_diets, form=form)


@app.route('/users/recipe', methods=['POST'])
def recipe():
    """Receives text from the recipe field in the HTML file"""
    

    recipe = dict()
    form = RecipeForm(request.form)

    if not g.user:
        flash("Session Expired. Log In to your Account Again", "danger")
        return redirect("/login")



    if form.validate_on_submit() and request.method == "POST":

        # Data posted from the recipe forms is received   
        
        recipe["title"] = form.title.data 
        recipe["servings"] = form.servings.data
        ingredients = [i.lstrip() for i in (",".join([form.ingredients.data]).split(","))]
        recipe["ingredients"] = ingredients
        recipe["instructions"] = form.instructions.data
        

        # userdiet = UserDiet.linkUserDiet(g.user.id, UserDiet.diet_id )
        # db.session.commit()
        
        # Converts data into json, so it can be submitted to the API. 
        request_data = json.dumps([recipe], indent=1)


        print(request_data)
                

    print(f"Validated:{form.validate_on_submit()}", request.method)
    return redirect(f'/users/{g.user.id}')

##############################################################################

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
