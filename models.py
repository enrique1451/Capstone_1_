"""SQLAlchemy models for NuTree."""

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()

def connect_db(app):
    db.app = app
    db.init_app(app)



class User(db.Model):
    """User in the system."""

    __tablename__ = "user"

    email = db.Column(db.Text, nullable=False, unique=True, primary_key=True)

    password = db.Column(db.Text, nullable=False,)

    username = db.Column(db.Text, nullable=False, unique=True,)

    userdiet = db.relationship("UserDiet")




    def __repr__(self):
        return f"<User #{self.username}: {self.email}>"


    @classmethod
    def signup(cls, email, password, username):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode("UTF-8")

        user = User(
            email=email,
            password=hashed_pwd,
            username=username
            )

        db.session.add(user)
        return user

        

    @classmethod
    def authenticate(cls, email, password):
        """Find user with `email` and `password`.

        If can"t find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(email=email).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False



class Diet(db.Model):
    """Database table for diets for the user to select."""

    __tablename__ = "diet"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    name = db.Column(db.String(140), nullable=False, unique=True)

    description = db.Column(db.Text, nullable=True, unique=True)

    user = db.relationship("User",secondary="userdiet", backref="diet", lazy="joined")

    userdiet = db.relationship("UserDiet")

      

    def __repr__(self):
        return "Diet(%r, %r)" % (self.name, self.description)


class UserDiet(db.Model):
    """Mapping users to diets."""

    __tablename__ = "userdiet" 
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    user_email = db.Column("user_email", db.ForeignKey("user.email"), primary_key=True)
    
    diet_id = db.Column("diet_id", db.ForeignKey("diet.id"), primary_key=True)

    def __repr__(self):
        return f'<UserDiet = user_email:{self.user_email} diet_id:{self.diet_id}>'




    

