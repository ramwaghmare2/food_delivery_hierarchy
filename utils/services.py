from models.manager import Manager
from models.distributor import Distributor
from models.super_distributor import SuperDistributor
from models.kitchen import Kitchen

def get_model_counts():
    """Returns a dictionary with counts of all models."""
    return {
        'manager_count': Manager.query.count(),
        'super_distributor_count': SuperDistributor.query.count(),
        'distributor_count': Distributor.query.count(),
        'kitchen_count': Kitchen.query.count(),
    }