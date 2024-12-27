from models import db, Admin, Manager, SuperDistributor, Distributor, Kitchen, Sales, Order, Customer, FoodItem
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import emit
from utils.services import allowed_file, get_image, get_user_query
from sqlalchemy.exc import IntegrityError
from utils.helpers import handle_error 
from datetime import datetime, timedelta, timezone
from functools import wraps
from collections import defaultdict
from models.order import OrderItem
from extensions import bcrypt
from base64 import b64encode
from functools import wraps
from sqlalchemy import func
from app import socketio
from .user_routes import role_required

admin_bp = Blueprint('admin_bp', __name__, static_folder='../static')
"""
ROLE_MODEL_MAP = {
    "Admin": Admin,
    "Manager": Manager,
    "SuperDistributor": SuperDistributor,
    "Distributor": Distributor,
    "Kitchen": Kitchen,
}

def get_model_by_role(role):
    return ROLE_MODEL_MAP.get(role)

"""

################################## Route for displaying admin dashboard ##################################
@admin_bp.route('/admin', methods=['GET'])
@role_required('Admin')
def admin_home():
    # Fetch session data
    role = session.get('role')
    user_id = session.get('user_id')
    user = get_user_query(role, user_id)
    encoded_image = get_image(role, user_id)

    # Initialize counts, totals, and sales data
    manager_count = 0
    super_distributor_count = 0
    distributor_count = 0
    kitchen_count = 0
    total_sales_amount = 0
    total_orders_count = 0
    quantity_sold = 0
    sales_data = []
    monthly_sales = []

    # Chart data initial values
    months = []
    total_sales = []
    kitchen_names = []
    order_counts = []
    pie_chart_labels = []
    pie_chart_data = []

    barChartData = {
        "labels": ["January", "February", "March", "April"],
        "values": [10, 20, 15, 30],
    }

    try:
        # Fetch counts
        manager_count = len(Manager.query.all())
        super_distributor_count = len(SuperDistributor.query.all())
        distributor_count = len(Distributor.query.all())
        kitchen_count = len(Kitchen.query.all())

        # Aggregate totals
        total_sales_amount = db.session.query(func.sum(Order.total_amount)).scalar() or 0
        total_orders_count = Order.query.count()
        quantity_sold = db.session.query(func.sum(OrderItem.quantity)).scalar() or 0

        # Sales data
        sales_data = db.session.query(
            Sales.sale_id,
            Sales.datetime,
            FoodItem.item_name,
            func.sum(OrderItem.price).label("total_price"),
            func.sum(OrderItem.quantity).label("total_quantity")
        ).join(OrderItem, Sales.item_id == OrderItem.item_id)\
        .join(FoodItem, OrderItem.item_id == FoodItem.id)\
        .group_by(Sales.sale_id, FoodItem.item_name, Sales.datetime)\
        .order_by(Sales.datetime.desc())\
        .all()

        # Monthly sales
        monthly_sales = db.session.query(
            func.date_format(Sales.datetime, '%Y-%m').label('month'),
            func.sum(Order.total_amount).label('total_sales')
        ).join(Order, Sales.sale_id == Order.order_id)\
        .group_by(func.date_format(Sales.datetime, '%Y-%m'))\
        .order_by(func.date_format(Sales.datetime, '%Y-%m'))\
        .all()

    except Exception as e:
        print(f"Error fetching data: {e}")

    # Render the admin dashboard template
    return render_template(
        'admin/admin_index.html',
        manager_count=manager_count,
        super_distributor_count=super_distributor_count,
        distributor_count=distributor_count,
        kitchen_count=kitchen_count,
        total_sales_amount=total_sales_amount,
        total_orders_count=total_orders_count,
        quantity_sold=quantity_sold,
        sales_data=sales_data,
        user_name=user.name,
        role=role,
        months=months,
        total_sales=total_sales,
        barChartData=barChartData,
        encoded_image=encoded_image,
        kitchen_names=kitchen_names,
        order_counts=order_counts,
        pie_chart_labels=pie_chart_labels,
        pie_chart_data=pie_chart_data
    )



################################## Sales Data Visualization ##################################
sales_bp = Blueprint('sales', __name__)
@sales_bp.route('/sales_report', methods=['GET'])
def sales_report():
    # Get the filter parameter from the query string
    filter_param = request.args.get('filter', 'today')  # Default to 'today' if no filter provided

    # Initialize the query
    query = Sales.query

    # Apply the filter if provided
    today = datetime.today()
    start_time, end_time = None, None
    total_sales_amount = 0
    total_orders_count = 0
    quantity_sold = 0
    
    if filter_param == 'today':
        start_time = datetime.combine(today, datetime.min.time())
        end_time = datetime.combine(today + timedelta(days=1), datetime.min.time())
    elif filter_param == 'yesterday':
        start_time = datetime.combine(today - timedelta(days=1), datetime.min.time())
        end_time = datetime.combine(today, datetime.min.time())
    elif filter_param == 'week':
        start_time = today - timedelta(days=today.weekday())
        end_time = start_time + timedelta(days=7)
    elif filter_param == 'month':
        start_time = datetime(today.year, today.month, 1)
        next_month = today.month % 12 + 1
        year = today.year + (today.month // 12)
        end_time = datetime(year, next_month, 1)

    if start_time and end_time:
        query = query.filter(Sales.datetime >= start_time, Sales.datetime < end_time)

    # Aggregate total sales and quantity sold
    total_sales_amount = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0
    total_orders_count = OrderItem.query.count()    
    quantity_sold = db.session.query(db.func.sum(OrderItem.quantity)).scalar() or 0

    # Get sales data for the table: Join OrderItem and FoodItem
    sales_data = db.session.query(
        Sales.sale_id,
        Sales.datetime,
        FoodItem.item_name,
        db.func.sum(OrderItem.price).label("total_price"),
        db.func.sum(OrderItem.quantity).label("total_quantity")
    ).join(OrderItem, Sales.item_id == OrderItem.item_id)\
    .join(FoodItem, OrderItem.item_id == FoodItem.id)\
    .group_by(Sales.sale_id, FoodItem.item_name, Sales.datetime)\
    .order_by(Sales.datetime.desc())\
    .all()

    # Get sales data for the line chart (sales by date)
    sales_by_date = db.session.query(
        func.date(Sales.datetime).label('sale_date'),
        func.sum(Order.total_amount).label('total_sales')
    ).filter(Sales.datetime >= start_time, Sales.datetime < end_time).group_by(func.date(Sales.datetime)).all()

    # Process sales data into a dictionary
    sales_by_date_dict = defaultdict(float)
    for sale in sales_by_date:
        sales_by_date_dict[sale.sale_date] += float(sale.total_sales)

    # Convert the sales data (for table and chart)
    dates = [str(date) for date in sales_by_date_dict.keys()] if sales_by_date_dict else ["No Data"]
    sales = list(sales_by_date_dict.values()) if sales_by_date_dict else [0]

    return render_template(
        'admin/sales_report.html',
        total_sales_amount=total_sales_amount,
        total_orders_count=total_orders_count,
        quantity_sold=quantity_sold,
        filter_param=filter_param,  # Pass filter to the template
        sales_data=sales_data,
        dates=dates,
        sales=sales,
    )

################################## Orders data visualization API ##################################
orders_bp = Blueprint('orders', __name__, url_prefix='/sales')

import sqlalchemy as sa

@orders_bp.route('/list', methods=['GET'])
def order_list():
    page = request.args.get('page', 1, type=int)
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
            status_query = Order.query.filter(Order.order_status == order_status)
            query = query.intersect(status_query)
            exception_message = f"No orders available with status '{order_status}'"
        else:
            exception_message = f"Invalid status filter: '{order_status}"

    orders = query.paginate(page=page, per_page=10)

    if not orders.items:
        return render_template('admin/order_list.html', orders=None, exception_message=exception_message)
    
    return render_template('admin/order_list.html', orders=orders, exception_message=None)


################################## View Details ##################################
@admin_bp.route('/view-details/<int:user_id>', methods=['GET'])
def view_details(user_id):
    id = session.get('user_id')
    role = session.get('role')
    user_name = get_user_query(role, id)
    encoded_image = get_image(role, id)

    # Fetch the user (manager)
    user = Manager.query.filter_by(id=user_id).first()
    
    # Get Super Distributors for the manager
    sd = SuperDistributor.query.filter(SuperDistributor.manager_id == user.id).all()
    sd_ids = [s.id for s in sd]
    
    # Get Distributors for the Super Distributors
    distributors = Distributor.query.filter(Distributor.super_distributor.in_(sd_ids)).all()
    distributor_ids = [distributor.id for distributor in distributors]
    
    # Get Kitchens for the Distributors
    kitchens = Kitchen.query.filter(Kitchen.distributor_id.in_(distributor_ids)).all()
    kitchen_ids = [kitchen.id for kitchen in kitchens]
    
    # Get Sales data for the Kitchens
    sales_k = Sales.query.filter(Sales.kitchen_id.in_(kitchen_ids)).all()

    # Extract all order_ids from the sales data
    order_ids = [sale.order_id for sale in sales_k]
    
    # Get Orders data based on the order_ids
    orders = Order.query.filter(Order.order_id.in_(order_ids)).all()

    # Helper function to calculate total sales for a given list of kitchens
    def calculate_total_sales(kitchens_list):
        total_sales = 0
        for kitchen in kitchens_list:
            # Find the sales corresponding to this kitchen
            kitchen_sales = [sale for sale in sales_k if sale.kitchen_id == kitchen.id]
            
            # Collect orders related to these sales
            kitchen_orders = [order for order in orders if order.order_id in [sale.order_id for sale in kitchen_sales]]
            
            # Sum the total amount of orders for this kitchen
            total_sales += sum(order.total_amount for order in kitchen_orders)
        return total_sales

    # Create super distributor data with sales included
    super_distributor_data = [
        {
            'super_distributor_name': super_distributor.name,
            'total_sales': calculate_total_sales(
                [kitchen for distributor in distributors if distributor.super_distributor == super_distributor.id
                    for kitchen in kitchens if kitchen.distributor_id == distributor.id]
            )
        }
        for super_distributor in sd
    ]

    # Create distributor data with sales included
    distributor_data = [
        {
            'distributor_name': distributor.name,
            'super_distributor_name': distributor.super_distributors.name,
            'total_sales': calculate_total_sales(
                [kitchen for kitchen in kitchens if kitchen.distributor_id == distributor.id]
            )
        }
        for distributor in distributors
    ]

    # Create kitchen data with sales included
    kitchen_data = [
        {
            'kitchen_name': kitchen.name,
            'distributor_name': kitchen.distributors.name,
            'total_sales': calculate_total_sales([kitchen])
        }
        for kitchen in kitchens
    ]

    details = 'Manager'

    return render_template('view_details.html',
                           role=role,
                           user_name=user_name.name,
                           encoded_image=encoded_image,
                           user=user,
                           details=details,
                           super_distributors=super_distributor_data,
                           distributors=distributor_data,
                           kitchens=kitchen_data,
                           )

