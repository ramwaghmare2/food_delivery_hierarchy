from flask import Flask
from flask_socketio import SocketIO
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from models import db
import os
from datetime import timedelta

socketio = SocketIO(cors_allowed_origins="*", ping_interval=25, ping_timeout=10)  # Declare SocketIO globally
bcrypt = Bcrypt()
def create_app():
    app = Flask(__name__, static_url_path='/static', static_folder='static')
    app.config.from_object('config.Config')
    app.secret_key = os.environ.get("SECRET_KEY", "default_secret_key")


    #app.permanent_session_lifetime = timedelta(minutes=30)

    socketio.init_app(app)
    app.socketio = socketio
    bcrypt.init_app(app)
    db.init_app(app)
    Migrate(app, db)

    # Register blueprints
    from routes import create_app_routes
    create_app_routes(app)

    return app

if __name__ == "__main__":
    app = create_app()
    socketio.run(app, debug=True)
