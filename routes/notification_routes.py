# routes/notification_routes.py

from flask import Blueprint, request, jsonify, session
from models import db, Notification

notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/notifications', methods=['GET'])
def get_notifications():
    from models import Notification
    role = request.args.get('role')
    notification_type = request.args.get('type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = Notification.query

    if role:
        query = query.filter(Notification.role == role)
    if notification_type:
        query = query.filter(Notification.notification_type == notification_type)
    if start_date:
        query = query.filter(Notification.created_at >= start_date)
    if end_date:
        query = query.filter(Notification.created_at <= end_date)

    notifications = query.order_by(Notification.created_at.desc()).all()
    return jsonify([n.to_dict() for n in notifications])


@notification_bp.route('/notifications/<int:id>/mark-as-read', methods=['POST'])
def mark_as_read(id):
    notification = Notification.query.get(id)
    if notification and session.get('user_id') == notification.user_id:
        notification.is_read = True
        db.session.commit()
        return jsonify({'message': 'Notification marked as read.'})
    return jsonify({'error': 'Notification not found or unauthorized.'}), 404

@notification_bp.route('/notifications/delete', methods=['POST'])
def delete_notifications():
    user_id = request.json.get('user_id')
    Notification.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return jsonify({'message': 'Notifications deleted successfully.'})
