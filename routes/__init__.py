from .admin import admin_bp
from .customer import customer_bp
from .distributor import distributor_bp
from .kitchen import kitchen_bp
from .manager import manager_bp
from .super_distributor import super_distributor_bp
from .cuisine import cuisine_bp
from .order import order_bp
from .food_item import food_item_bp
from .admin import sales_bp, orders_bp
from .dashboard import dashboard_bp

def create_app_routes(app):
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(customer_bp, url_prefix='/customer')
    app.register_blueprint(distributor_bp, url_prefix='/distributor')
    app.register_blueprint(kitchen_bp, url_prefix='/kitchen')
    app.register_blueprint(manager_bp, url_prefix='/manager')
    app.register_blueprint(super_distributor_bp, url_prefix='/super_distributor')
    app.register_blueprint(cuisine_bp, url_prefix='/cuisine')
    app.register_blueprint(order_bp, url_prefix='/order')
    app.register_blueprint(food_item_bp, url_prefix='/fooditem')
    app.register_blueprint(sales_bp, url_prefix='/admin/sales')  # Updated prefix
    app.register_blueprint(orders_bp, url_prefix='/admin/orders')  # Updated prefix
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    
