from models.manager import Manager
from models.distributor import Distributor
from models.super_distributor import SuperDistributor
from models.kitchen import Kitchen

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
