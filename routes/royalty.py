from models import db
from datetime import datetime
from functools import wraps
from flask import request, jsonify, Blueprint
from models.royalty import RoyaltySettings, RoyaltyWallet
from admin import admin_bp


################################## Decorators for Role-Based Access ##################################
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_role = request.headers.get('Role')
        if user_role != 'Admin':
            return jsonify({"error": "Access denied"}), 403
        return f(*args, **kwargs)
    return decorated_function

################################## Update Royalty Percentage (Admin-Only) ##################################
@admin_bp.route('/admin/update-royalty', methods=['PUT'])
@admin_only
def update_royalty():
    data = request.json
    new_percentage = data.get("royalty_percentage")
    if not new_percentage or not (0 < new_percentage <= 100):
        return jsonify({"error": "Invalid royalty percentage"}), 400

    setting = RoyaltySettings.query.first()
    if not setting:
        setting = RoyaltySettings(royalty_percentage=new_percentage)
        db.session.add(setting)
    else:
        setting.royalty_percentage = new_percentage

    db.session.commit()
    return jsonify({"message": "Royalty percentage updated successfully"})


################################## Route for Distribute Royalty After Kitchen Close ##################################
@admin_bp.route('/kitchen/close-day', methods=['POST'])
def close_day():
    data = request.json
    kitchen_id = data.get("kitchen_id")
    total_sales = data.get("total_sales")

    if not kitchen_id or not total_sales:
        return jsonify({"error": "Missing data"}), 400

    if total_sales < 1000:
        return jsonify({"message": "Sales did not reach the minimum threshold"}), 200

    setting = RoyaltySettings.query.first()
    if not setting:
        return jsonify({"error": "Royalty settings not found"}), 500

    royalty_percentage = setting.royalty_percentage
    royalty_per_entity = (total_sales * royalty_percentage / 100) / 4

    roles = ['Admin', 'Manager', 'Super Distributor', 'Distributor']
    for role in roles:
        wallet = RoyaltyWallet.query.filter_by(role=role).first()
        if not wallet:
            wallet = RoyaltyWallet(entity_id=None, role=role, royalty_amount=0.0)
            db.session.add(wallet)
        wallet.royalty_amount += royalty_per_entity
        wallet.updated_at = datetime.utcnow()

    db.session.commit()
    return jsonify({"message": "Royalty distributed successfully"})