import os, json, requests
from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from forms import UserAddForm, LoginForm, RecipeForm, SelectDietsForm
from models import db, connect_db, User, Diet, UserDiet
from secrets import API_KEY


CURR_USER_KEY = "user_id"
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

BASE_URL = "https://api.spoonacular.com"

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
        return redirect(f'/users/{g.user.id}')
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
            flash("user already exists in our database. If password has been forgotten, please request a password reset", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect(f"/users/dietSelection")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """user login."""

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



@app.route('/delete_user', methods=["GET", "POST"])
def delete_user():
    """ delete user """
    if not g.user:
        flash("Account deletion only possible while logged-in", "danger")
        return redirect("/login")

    user = User.query.get_or_404(g.user.id)

    db.session.delete(user)
    db.session.commit()
    session.pop(CURR_USER_KEY)
    flash(f"{g.user.username} account has been deleted from out platform")
    return redirect('/signup')

    


@app.route('/users/dietSelection', methods=["GET", "POST"]) 
def select_diet():
    """ Diets presentation and selection form for new users"""
    
    # available_diets = Diet.query.all()
    form = SelectDietsForm()
    user = g.user

    if form.validate_on_submit() and request.method == "POST":

            try:
                print(form.diets.data)
                for diet in form.diets.data:
                                     
                    userdiet = UserDiet.linkUserDiet(
                        userid = user.id, 
                        dietid = diet.id,
                        )
                    db.session.commit()

            except IntegrityError:
                db.session.rollback()
            
    return render_template('users/dietSelection.html', form=form) 
    

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
    chosen_diets = (Diet.query.join(UserDiet).filter(user_id == user.id).all())

    return render_template('users/user_home.html', user=user, chosen_diets=chosen_diets, form=form)


@app.route('/users/recipe/<int:user_id>', methods=['POST'])
def recipe(user_id):

    # Receives text from the the client form
    recipe = dict()
    form = RecipeForm(request.form)

    if not g.user:
        flash("Session Expired. Log In to your Account Again", "danger")
        return redirect("/login")

    # Data posted from the recipe forms is received  
    if form.validate_on_submit() and request.method == "POST":
 
        recipe["title"] = form.title.data 
        recipe["servings"] = form.servings.data

    #removes undesirable symbols from form to minimize API reading errors
        ingredients = [i.lstrip() for i in (",".join([form.ingredients.data]).split(","))]
        recipe["ingredients"] = ingredients
        recipe["instructions"] = form.instructions.data
        

    # Converts data type from dict into plain text, so it can be submitted to the API. 
        recipe = str(recipe)


    #contact API and sends POST request to parse and analyze ingredients in recipe
        response = requests.post(f"{BASE_URL}/recipes/analyze", params={"apiKey": API_KEY, "language":"en", "includeNutrition": False} , headers={"Content-Type": "text/plain"}, data=recipe)

        analyzed_recipe = json.loads(response.text)
        recipe_properties = analyzed_recipe.keys()
        recipe_non_compliant_diets = [];
        chosen_diets = (Diet.query.join(UserDiet).filter(user_id == g.user.id).all())

        for p in recipe_properties:
            if analyzed_recipe[p] == False:
                recipe_non_compliant_diets.append(p.lower())
            else:
                continue

        print(f"The diet is not compliant with {recipe_non_compliant_diets} diets")
        print(f"Validated:{form.validate_on_submit()}", f"Request Method: {request.method}")

        return render_template("/users/result.html", chosen_diets=chosen_diets, recipe_non_compliant_diets=recipe_non_compliant_diets)



# 2½ tablespoons kosher salt,
# 1 tablespoon dry mustard,
# 1 tablespoon paprika,
# ½ teaspoon cayenne pepper,
# ½ teaspoon freshly ground black pepper, 
# 8 pounds baby back pork ribs (8 racks) or St. Louis-style spareribs (4 racks),
# Low-salt chicken broth (optional),
# 1½ cups store-bought or homemade barbecue sauce

# "instructions": "Bring a large pot of water to a boil and season generously with salt. Add the pasta to the water once boiling and cook until al dente. Reserve 2 cups of cooking water and drain the pasta. "

# WATER:
# {
#     "vegetarian": true,
#     "vegan": true,
#     "glutenFree": true,
#     "dairyFree": true,
#     "veryHealthy": false,
#     "cheap": true,
#     "veryPopular": false,
#     "sustainable": false,
#     "weightWatcherSmartPoints": 0,
#     "gaps", "": "no",
#     "lowFodmap": true,
#     "aggregateLikes": 0,
#     "spoonacularScore": 42,
#     "healthScore": 0,
#     "pricePerServing": 0,
#     "extendedIngredients"
# }

##############################################################################

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
