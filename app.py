from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db
from flask_bcrypt import Bcrypt
import os

bcrypt = Bcrypt()
def create_app():
    app = Flask(__name__ ,static_url_path='/static', static_folder='static')
    bcrypt = Bcrypt(app)
    app.config.from_object('config.Config')

    db.init_app(app)

    # Initialize Flask-Migrate
    migrate = Migrate(app, db)
    bcrypt.init_app(app)

    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static/images')
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

    from routes import create_app_routes
    # Register routes
    create_app_routes(app)

    return app



if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
