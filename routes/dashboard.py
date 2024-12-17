from models import db, Admin, Manager, SuperDistributor, Distributor, Kitchen, Sales, Order, Customer, FoodItem
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash, current_app
from flask_socketio import emit
from utils.services import allowed_file, get_image, get_user_query
from sqlalchemy.exc import IntegrityError
from utils.helpers import handle_error 
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from models.order import OrderItem
from functools import wraps
from sqlalchemy import func
from app import socketio
from .admin import role_required

dashboard_bp = Blueprint('dashboard', __name__, static_folder='../static')
################################## Route for displaying admin dashboard ##################################
@dashboard_bp.route('/admin', methods=['GET'])
@role_required('Admin')
def admin_dashboard():
    # Fetch session data
    role = session.get('role')
    user_id = session.get('user_id')
    user = get_user_query(role, user_id)
    encoded_image = get_image(role, user_id)

    # Initialize counts, totals, and sales data
    total_sales_amount, total_orders_count, quantity_sold = 0, 0, 0
    sales_data = []
    sales_by_item = {"labels": [], "values": []}
    quantity_sold_over_time = {"labels": [], "values": []}
    top_item_names, top_item_quantities = [], []
    distribution_labels, distribution_values = [], []
    performance_dates, total_revenues, monthly_sales = [], [], []
    months, total_sales, kitchen_names, order_counts = [], [], [], []
    barChartData = {"labels": ["January", "February", "March", "April"], "values": [10, 20, 15, 30]}

    try:
        # Aggregate totals
        total_sales_amount = db.session.query(func.sum(Order.total_amount)).scalar() or 0
        total_orders_count = OrderItem.query.count()
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

        # Chart 1: Sales by Item Name
        sales_by_item_query = db.session.query(
            FoodItem.item_name,
            func.sum(OrderItem.price * OrderItem.quantity).label('total_sales')
        ).join(OrderItem, FoodItem.id == OrderItem.item_id)\
        .group_by(FoodItem.item_name).all()

        sales_by_item = {
            "labels": [item[0] for item in sales_by_item_query],
            "values": [float(item[1]) for item in sales_by_item_query]
        }
        print("sales_by_item: ",sales_by_item)

        # Chart 2: Quantity Sold Over Time
        quantity_sold_query = db.session.query(
            func.date(FoodItem.created_at).label('sale_date'),
            func.sum(OrderItem.quantity).label('total_quantity')
        ).group_by(func.date(FoodItem.created_at)).all()

        # Ensure that query results are processed
        quantity_sold_over_time = {
            "labels": [str(row[0]) for row in quantity_sold_query],  # Convert dates to strings
            "values": [int(row[1]) for row in quantity_sold_query]  # Ensure values are integers
        }
        print("quantity_sold_over_time: ",quantity_sold_over_time)

        # Chart 3: Top-Selling Items
        top_selling_items_query = db.session.query(
            FoodItem.item_name,
            func.sum(OrderItem.quantity).label('total_quantity')
        ).join(OrderItem, FoodItem.id == OrderItem.item_id)\
        .group_by(FoodItem.item_name)\
        .order_by(func.sum(OrderItem.quantity).desc())\
        .limit(10).all()

        top_item_names = [item[0] for item in top_selling_items_query]
        top_item_quantities = [int(item[1]) for item in top_selling_items_query]

        top_selling_items = {
            'labels': top_item_names,
            'values': top_item_quantities,
        }
        print("top_selling_items: ",top_selling_items)

        # Chart 4: Sales Distribution by Item
        sales_distribution = db.session.query(
            FoodItem.item_name,
            func.sum(OrderItem.price * OrderItem.quantity).label('total_sales')
        ).join(OrderItem, FoodItem.id == OrderItem.item_id)\
        .group_by(FoodItem.item_name).all()

        distribution_labels = [item[0] for item in sales_distribution]
        distribution_values = [float(item[1]) for item in sales_distribution]
        print("sales_distribution: ",sales_distribution)

        # Chart 5: Daily Sales Performance
        daily_sales_performance = db.session.query(
            func.date(FoodItem.created_at).label('sale_date'),
            func.sum(FoodItem.price * OrderItem.quantity).label('total_revenue')
        ).group_by(func.date(FoodItem.created_at))\
        .order_by(func.date(FoodItem.created_at)).all()

        performance_dates = [str(row[0]) for row in daily_sales_performance]
        total_revenues = [float(row[1]) for row in daily_sales_performance]

    except Exception as e:
        print(f"Error fetching data: {e}")

    # Render the admin dashboard template
    return render_template(
        'admin/admin_dashboard.html',
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
        sales_by_item=sales_by_item,
        top_selling_items = top_selling_items,
        quantity_sold_over_time=quantity_sold_over_time,
        #top_selling_items={"labels": top_item_names, "values": top_item_quantities},
        sales_distribution={"labels": distribution_labels, "values": distribution_values},
        daily_sales_performance={"labels": performance_dates, "values": total_revenues}
    )

@dashboard_bp.route('/manager', methods=['GET'])
@role_required('Manager')  
def manager_dashboard():
    from models import SuperDistributor, Distributor, Kitchen
    super_distributors = SuperDistributor.query.all()
    distributors = Distributor.query.all()
    kitchens = Kitchen.query.all()

    return render_template('manager/manager_dashboard.html', 
                           super_distributors=super_distributors, 
                           distributors=distributors, 
                           kitchens=kitchens)


@dashboard_bp.route('/super_distributor', methods=['GET'])
@role_required('SuperDistributor')  
def super_distributor_dashboard():
    from models import Distributor, Kitchen
    distributors = Distributor.query.all()
    kitchens = Kitchen.query.all()

    return render_template('admin/super_distributor_dashboard.html', 
                           distributors=distributors, 
                           kitchens=kitchens)


@dashboard_bp.route('/distributor', methods=['GET'])
@role_required('Distributor')  
def distributor_dashboard():
    from models import Kitchen
    kitchens = Kitchen.query.all()

    return render_template('admin/distributor_dashboard.html', 
                           kitchens=kitchens)


@dashboard_bp.route('/kitchen', methods=['GET'])
@role_required('Kitchen')  
def kitchen_dashboard():
    from models import Kitchen
    kitchens = Kitchen.query.filter_by(id=session['user_id']).all()  

    return render_template('admin/kitchen_dashboard.html', kitchens=kitchens)

