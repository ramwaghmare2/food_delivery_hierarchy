from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import individual models
from .admin import Admin
from .customer import Customer
from .distributor import Distributor
from .kitchen import Kitchen
from .manager import Manager
from .super_distributor import SuperDistributor
from .cuisine import Cuisine
from .sales import Sales
from .order import Order
from .food_item import FoodItem
from .order import OrderItem
from .activitylog import ActivityLog
