from ast import Import
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db
from flask_bcrypt import Bcrypt
import os
from extensions import bcrypt, socketio
#from flask_socketio import SocketIO
from routes.admin import socketio
# from routes.admin import register_signals
# from extensions import socketio
from flask_login import LoginManager, login_manager
from models import Admin

login_manager = LoginManager()

# Define the user_loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    # This function loads the user from the database by their user_id
    return Admin.query.get(int(user_id))

def create_app():
    app = Flask(__name__ ,static_url_path='/static', static_folder='static')
    
    login_manager.init_app(app)
    #login_manager.login_view = "auth.login"  # Update with your actual login route's name

    bcrypt = Bcrypt(app)
    app.config.from_object('config.Config')
    app.secret_key = "asf18fsf8s14fsafsdf48sd"

    db.init_app(app)

    # Initialize Flask-Migrate
    migrate = Migrate(app, db)
    #socketio.init_app(app)

    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static/images')
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

    from routes import create_app_routes
    # register_signals(app)

    # Register all blueprints through create_app_routes
    create_app_routes(app)  # This will register admin_bp and other blueprints

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
