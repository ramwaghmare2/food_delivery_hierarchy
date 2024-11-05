from flask import Flask
from models import db
from routes import create_app_routes

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    create_app_routes(app)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
