from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_seeder import FlaskSeeder
from flask_restx import Api

app = Flask(__name__)
api = Api(app)

app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

seeder = FlaskSeeder()
seeder.init_app(app, db)

from app.model import todo, user
from app import routes