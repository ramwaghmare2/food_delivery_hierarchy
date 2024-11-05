from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import individual models
from .admin import Admin
from .customer import Customer
from .distributor import Distributor
from .kitchen import Kitchen
from .manager import Manager
