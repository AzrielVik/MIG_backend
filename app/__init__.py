from flask import Flask
from .extensions import db, migrate

def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mig.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db) 

    # IMPORTANT: load models
    from app.models import models

    with app.app_context():
        db.create_all()

    return app
