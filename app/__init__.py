from flask import Flask
from flask_cors import CORS  # Added this import
from app.extensions import db, migrate

def create_app():
    app = Flask(__name__)

    # Enable CORS for all routes so your Flutter frontend can connect
    CORS(app) 

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mig.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db)

    # load models so Alembic can see them
    from app.models import models

    # register routes blueprint
    from app.routes import routes
    app.register_blueprint(routes)

    return app