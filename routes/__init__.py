from flask import Blueprint
from .admin import admin_bp
from .customer import customer_bp
from .distributor import distributor_bp
from .kitchen import kitchen_bp
from .manager import manager_bp

def create_app_routes(app):
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(customer_bp, url_prefix='/customer')
    app.register_blueprint(distributor_bp, url_prefix='/distributor')
    app.register_blueprint(kitchen_bp, url_prefix='/kitchen')
    app.register_blueprint(manager_bp, url_prefix='/manager')
