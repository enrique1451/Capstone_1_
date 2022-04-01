import os, json, requests
from flask_bootstrap import Bootstrap5
from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from forms import UserAddForm, LoginForm, RecipeForm, UserSelectedDiets
from models import db, connect_db, User, Diet, UserDiet
from secrets import API_KEY


app = Flask(__name__)
bootstrap = Bootstrap5(app)
CURR_USER_KEY = "user_id"






# Get DB_URI from environment variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///nutree'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
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



@app.route('/signup', methods = ["GET", "POST"])
def signup():

    """username user signup.
    Create new user and add to DB. Redirect to home page.
    If form not valid, present form.
    If the there already is a user with that username: flash message
    and re-present form.
    """
    form = UserAddForm()

    if form.validate_on_submit() and request.method == "POST":
        try:
            user = User.signup(
                email = form.email.data,
                password = form.password.data,
                username  =  form.username.data,                                 
               )
            db.session.commit()

        except IntegrityError:
            return render_template('users/signup.html', form = form)

        do_login(user)
        return redirect(f"/users/{user_id}")

    else:
        return render_template('users/signup.html', form = form)




@app.route('/login', methods = ["GET", "POST"])
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

    return render_template('users/signup.html', form = form)




@app.route('/delete_user', methods = ["GET", "POST"])
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




@app.route('/users/dietSelection/<int:user_id>', methods = ["GET"]) 
def diets_list(user_id):
    """ Diets presentation and selection form for new users"""
    diets = Diet.query.all()
    form = UserSelectedDiets()
    user = g.user
     
    return render_template('users/dietSelection.html', form = form, diets=diets, user=user) 




@app.route('/users/dietSelection/<int:user_id>', methods=["POST"]) 
def bind_diets_to_profile(user_id):

    user = g.user
    selected_diets  = request.form.getlist('check')

    try:
        for diet in selected_diets:
                                
            userdiet = UserDiet.linkUserDiet(
                userid = user.id, 
                dietid = diet,
                )
            db.session.commit()
            flash(f"{diet} has been added to profile", "success")

    except IntegrityError:
        db.session.rollback()



    return redirect(f'/users/{user_id}')


        
     
#     return render_template('users/dietSelection.html', form = form, diets=diets, user=user) 
@app.route('/logout')
def logout():
    """username logout of user."""
    do_logout()
    flash("You have been successfully logged out", info)

    return redirect("/")

##############################################################################
# General user routes: 

@app.route('/users/<int:user_id>', methods=['GET'])
def user_home(user_id):
    """Show user homepage."""
    
    form = RecipeForm()
    user = User.query.get_or_404(user_id)
    chosen_diets = (Diet.query.join(UserDiet).filter_by(user_id = user.id).all())

    if not g.user:
        flash("Session Expired. Log In to your Account Again", "danger")
        return redirect("/login")

    if g.user.id != user_id or user == None:
        flash("You dont have authorized access to this account", "danger")
        return redirect("/login")

    print(g.user.id == user_id)

    # Getting user's diets from database

    return render_template(
        'users/user_home.html', 
        user = user, 
        chosen_diets = chosen_diets,
        form = form
        )


@app.route('/users/recipe/<int:user_id>', methods = ['POST'])
def recipe(user_id):

    # Receives text from the the client form    
    recipe  =  dict()
    form  =  RecipeForm(request.form)
    

    if not g.user:
        flash("Session Expired. Log In to your Account Again", "danger")
        return redirect("/login")

    # Data posted from the recipe forms is received  
    if form.validate_on_submit() and request.method == "POST":
 
        recipe["title"] = form.title.data 
        recipe["servings"] = form.servings.data
        print(recipe["title"], recipe["servings"])

    #removes undesirable symbols from form to minimize API reading errors
        ingredients = [i.lstrip() for i in (",".join([form.ingredients.data]).split(","))]
        recipe["ingredients"] = ingredients
        recipe["instructions"] = form.instructions.data
        

    # Converts data type from dict into plain text, so it can be submitted to the API. 
        recipe = str(recipe)


    #contact API and sends POST request to parse and analyze ingredients in recipe
        response = requests.post(
            f"{BASE_URL}/recipes/analyze", 
            params = {"apiKey": API_KEY, "language":"en", "includeNutrition": False}, 
            headers = {"Content-Type": "text/plain"}, data=recipe
            )

        analyzed_recipe = json.loads(response.text)
        recipe_properties = analyzed_recipe.keys()
        recipe_non_compliant_diets = [];
        chosen_diets = (Diet.query.join(UserDiet).filter_by(user_id = user.id).all())

        for p in recipe_properties:
            if analyzed_recipe[p] == False:
                recipe_non_compliant_diets.append(p.lower())
            else:
                continue

        # print(f"The diet is not compliant with {recipe_non_compliant_diets} diets")
        # print(f"Validated:{form.validate_on_submit()}", f"Request Method: {request.method}")

        return render_template(
            "/users/result.html",
            chosen_diets = chosen_diets, 
            recipe_non_compliant_diets = recipe_non_compliant_diets, 
            user = g.user
            )




##############################################################################

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
