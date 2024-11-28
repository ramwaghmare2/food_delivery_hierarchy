import os
from models import db
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from routes import create_app_routes

def create_app():
    app = Flask(__name__ ,static_url_path='/static', static_folder='static')

    bcrypt = Bcrypt(app)
    app.config.from_object('config.Config')
    app.secret_key = "asf18fsf8s14fsafsdf48sd"

    db.init_app(app)

    # Initialize Flask-Migrate
    migrate = Migrate(app, db)

    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static/images')
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

    # Register all blueprints through create_app_routes
    create_app_routes(app)  # This will register admin_bp and other blueprints

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
