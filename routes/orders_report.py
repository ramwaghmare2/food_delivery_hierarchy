###################################### Importing Required Libraries ###################################
from models import db, Manager, SuperDistributor, Distributor, Kitchen, Sales, Order, Customer, FoodItem
from flask import Blueprint, request, session, render_template
from utils.services import get_image, get_user_query
from datetime import datetime, timedelta
from utils.notification_service import check_notification
from collections import defaultdict
from models.order import OrderItem
from sqlalchemy import func ,desc
from .user_routes import role_required
from sqlalchemy import and_

###################################### Blueprint for Orders data Visualization API ####################
orders_bp = Blueprint('orders', __name__, url_prefix='/sales')

###################################### Orders data visualization API ##################################
@orders_bp.route('/list', methods=['GET'])
def order_list():
    role = session.get('role')
    user_id = session.get('user_id')
    user = get_user_query(role, user_id)
    encoded_image = get_image(role, user_id)
    search_query = request.args.get('search', '', type=str)
    filter_by = request.args.get('filter_by', 'all')
    order_status = request.args.get('status', '', type=str)

    query = Order.query
    exception_message = None

    if search_query:
        if search_query.isdigit():  
            if filter_by == 'user_id':
                query = query.filter(Order.user_id == int(search_query))
                exception_message = f"No Orders available for User ID {search_query}"
            elif filter_by == 'order_id':
                query = query.filter(Order.order_id == int(search_query))
                exception_message = f"No Orders available for Order ID {search_query}"
            elif filter_by == 'kitchen_id':
                query = query.filter(Order.kitchen_id == int(search_query))
                exception_message = f"No Orders available for Kitchen ID {search_query}"
            else:  
                query = Order.query
        else:
            query = query.join(Customer).filter(Customer.name.ilike(f'%{search_query}'))
            exception_message = f"No orders available for customer matching '{search_query}'"

    if order_status:
        if order_status in ['pending', 'processing', 'cancelled', 'completed']:
            query = query.filter(Order.order_status == order_status)
            exception_message = f"No orders available with status '{order_status}'"
        else:
            exception_message = f"Invalid status filter: '{order_status}'"
    query = query.order_by(Order.created_at.desc())
    orders = query.all()  # Fetch all records instead of paginated results

    total_order_count = Order.query.count()
    total_quantity_sold = db.session.query(func.sum(OrderItem.quantity)).scalar() or 0
    total_completed_orders = Order.query.filter(Order.order_status == 'completed').count()
    total_cancelled_orders = Order.query.filter(Order.order_status == 'cancelled').count()
    total_pending_orders = Order.query.filter(Order.order_status == 'pending').count()

    if not orders:
        return render_template('admin/order_list.html', orders=None, exception_message=exception_message)
    
    return render_template('admin/order_list.html', 
                           orders=orders, 
                           exception_message=None,
                           total_order_count=total_order_count,
                           total_quantity_sold=total_quantity_sold,
                           total_completed_orders=total_completed_orders,
                           total_cancelled_orders=total_cancelled_orders,
                           total_pending_orders=total_pending_orders,
                           user_name=user.name,
                           role=role,
                           encoded_image=encoded_image,
                           )
