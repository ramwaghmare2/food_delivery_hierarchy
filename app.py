from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db
from routes import create_app_routes  # Import create_app_routes from routes

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    app.secret_key = "asf18fsf8s14fsafsdf48sd"

    db.init_app(app)

    # Initialize Flask-Migrate
    migrate = Migrate(app, db)

    # Register all blueprints through create_app_routes
    create_app_routes(app)  # This will register admin_bp and other blueprints

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
