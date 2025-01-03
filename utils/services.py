from models.manager import Manager
from models.distributor import Distributor
from models.super_distributor import SuperDistributor
from models.kitchen import Kitchen
from models.admin import Admin, db
from models import Sales, Order
from sqlalchemy import func, and_
from base64 import b64encode
from datetime import datetime, time

def get_model_counts():
    """Returns a dictionary with counts of all models."""
    return {
        'manager_count': Manager.query.filter_by(status='activated').count(),
        'super_distributor_count': SuperDistributor.query.filter_by(status='activated').count(),
        'distributor_count': Distributor.query.filter_by(status='activated').count(),
        'kitchen_count': Kitchen.query.filter_by(status='activated').count(),
    }

# Function for image storage
def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

################################## globally defined role_model_map ##################################

ROLE_MODEL_MAP = {
    "Admin": Admin,
    "Manager": Manager,
    "SuperDistributor": SuperDistributor,
    "Distributor": Distributor,
    "Kitchen": Kitchen,
}

def get_model_by_role(role):
    return ROLE_MODEL_MAP.get(role)


def get_image(role,user_id):

    user_model = ROLE_MODEL_MAP.get(role)
    if not user_model:
        return {'error': 'Invalid role provided'}

    user_instance = user_model.query.get(user_id)
    if not user_instance:
        return {'error': 'User not found'}

    # Encode the image if it exists
    encoded_image = None
    if user_instance.image:
        encoded_image = b64encode(user_instance.image).decode('utf-8')
        
    return encoded_image


def get_user_query(role, user_id):
       
    model = ROLE_MODEL_MAP.get(role)
    
    if not model:
        raise ValueError(f"Invalid role: {role}. Please check the role and try again.")

    user = model.query.filter_by(id=user_id).first()

    return user


def today_sale(user_id):

    
    today_start = datetime.combine(datetime.today(), time.min)  # Midnight
    today_end = datetime.combine(datetime.today(), time.max)   # 11:59 PM

    # Query to calculate total sales
    today_total_sales = db.session.query(
            func.sum(Order.total_amount)
        ).join(Sales, Sales.order_id == Order.order_id) \
         .filter(
            and_(
                Sales.kitchen_id == user_id,
                Sales.datetime >= today_start,
                Sales.datetime <= today_end
            )
         ).scalar()
    
    return today_total_sales