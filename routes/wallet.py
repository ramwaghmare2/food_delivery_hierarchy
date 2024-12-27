from flask import request, jsonify, Blueprint
from models.royalty import RoyaltySettings, RoyaltyWallet


wallet_bp = Blueprint('wallet_bp', __name__, static_folder='../static')

@wallet_bp.route('/wallet/view', methods=['GET'])
def view_wallet():
    role = request.args.get("role")
    wallet = RoyaltyWallet.query.filter_by(role=role).first()

    if not wallet:
        return jsonify({"error": "Wallet not found"}), 404

    return jsonify({
        "role": wallet.role,
        "royalty_amount": wallet.royalty_amount,
        "updated_at": wallet.updated_at
    })

@wallet_bp.route('/wallet/all', methods=['GET'])
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