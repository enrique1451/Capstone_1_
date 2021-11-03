import os
from models import User, Diet, UserDiet, db
from app import app


db.drop_all()
db.create_all()
