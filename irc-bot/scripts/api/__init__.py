
from flask import Flask
from scripts.db import db
from flask_restful import Api
from scripts.db.models import AddedServers

# Creating main flask and api...
app = Flask(__name__)
api = Api(app)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initiating the db...
db.init_app(app)
db.create_all(app=app)