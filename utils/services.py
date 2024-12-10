from models.manager import Manager
from models.distributor import Distributor
from models.super_distributor import SuperDistributor
from models.kitchen import Kitchen
from models.admin import Admin
from base64 import b64encode

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

def get_image(role,user_id):

    role_model_map = {
            "Admin": Admin,
            "Manager": Manager,
            "SuperDistributor": SuperDistributor,
            "Distributor": Distributor,
            "Kitchen": Kitchen
        }

    user_model = role_model_map.get(role)
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
    
    role_model_map = {
                "Admin": Admin,
                "Manager": Manager,
                "SuperDistributor": SuperDistributor,
                "Distributor": Distributor,
                "Kitchen": Kitchen
            }
            
    model = role_model_map.get(role)
    
    user = model.query.filter_by(id=user_id).first()

    return user