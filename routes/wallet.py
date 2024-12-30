from flask import request, jsonify, Blueprint, render_template, redirect, url_for, session
from models.royalty import RoyaltySettings, RoyaltyWallet
from models import Sales, Order, db
from utils.services import get_image, get_user_query, today_sale

from datetime import datetime, time


wallet_bp = Blueprint('wallet', __name__, static_folder='../static')

@wallet_bp.route('/view', methods=['GET'])
def view_wallet():
    role = session.get('role')
    user_id = session.get('user_id')
    image_data = get_image(role, user_id)
    user = get_user_query(role, user_id)

    wallet = RoyaltyWallet.query.filter_by(entity_id=user_id).first()

    today_total_sales = today_sale(user_id)


    return render_template('kitchen/wallet.html',
                           encoded_image=image_data,
                           user_name=user.name,
                           user_id=user_id,
                           total_sales=today_total_sales,
                           role=role
                           )

@wallet_bp.route('/all', methods=['GET'])
def view_all_wallets():
    wallets = RoyaltyWallet.query.all()
    return jsonify([
        {
            "role": wallet.role,
            "royalty_amount": wallet.royalty_amount,
            "updated_at": wallet.updated_at
        } for wallet in wallets
    ])


"""
# Initialization
@app.before_first_request
def create_tables():
    db.create_all()
    if not RoyaltySettings.query.first():
        db.session.add(RoyaltySettings(royalty_percentage=20.0))
        db.session.commit()
        
"""