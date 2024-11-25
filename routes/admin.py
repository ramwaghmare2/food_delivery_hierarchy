# from crypt import methods
from email.policy import default
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from models import db
from flask import Blueprint,render_template, flash
from models.order import OrderItem
from utils.helpers import handle_error #get_model_counts
from models import db 
from flask import Blueprint,render_template, flash
from utils.services import get_model_counts
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy.exc import IntegrityError
from models import Admin, Manager, SuperDistributor, Distributor, Kitchen, Sales, Order, Customer
from utils.services import allowed_file
from base64 import b64encode
from extensions import bcrypt
from datetime import datetime, timedelta
from collections import defaultdict
from flask_socketio import SocketIO, emit
from flask import current_app
from flask_login import user_logged_in, user_logged_out, current_user
from extensions import socketio

admin_bp = Blueprint('admin_bp', __name__, static_folder='../static')

# Helper function to create a user based on role
def create_user(data, role):
    from models import db  
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    try:
        if role == "Admin":
            from models import Admin  
            new_user = Admin(name=data['name'], email=data['email'], password=hashed_password, contact=data['contact'])
        elif role == "Manager":
            from models import Manager
            new_user = Manager(name=data['name'], email=data['email'], password=hashed_password, contact=data['contact'])
        elif role == "SuperDistributor":
            from models import SuperDistributor
            new_user = SuperDistributor(name=data['name'], email=data['email'], password=hashed_password, contact=data['contact'])
        elif role == "Distributor":
            from models import Distributor
            new_user = Distributor(name=data['name'], email=data['email'], password=hashed_password, contact=data['contact'])
        elif role == "Kitchen":
            from models import Kitchen
            new_user = Kitchen(name=data['name'], email=data['email'], password=hashed_password, contact=data['contact'])
        else:
            return None
        db.session.add(new_user)
        db.session.commit()
        return new_user
    except IntegrityError:
        db.session.rollback()
        return None

def role_required(required_roles):
    """
    Decorator to enforce access control based on the user role.
    `required_roles` can be a single role or a list of roles.
    """
    if isinstance(required_roles, str):
        required_roles = [required_roles]  # Convert to list if it's a single role

    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if 'role' not in session:
                return jsonify({"error": "Unauthorized access"}), 401
            if session['role'] not in required_roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            return fn(*args, **kwargs)

        return decorated_view

    return wrapper

# Route for displaying admin dashboard
from flask_login import current_user
from flask import render_template, session

@admin_bp.route('/admin', methods=['GET'])
@role_required('Admin')
def admin_dashboard():
    from models import Manager, SuperDistributor, Distributor, Kitchen  # Delayed imports
    user_name = session.get('user_name', 'User')
    role = session.get('role')

    # Get counts for managers, distributors, etc.
    manager_count = Manager.query.count()
    super_distributor_count = SuperDistributor.query.count()
    distributor_count = Distributor.query.count()
    kitchen_count = Kitchen.query.count()

    # Query sales and orders
    total_sales = Sales.query.all()  # Assuming you have a Sale model to track sales
    total_orders = Order.query.all()

    total_sales_amount = sum([sale.price for sale in total_sales])  # Adjust field as necessary
    total_orders_count = len(total_orders)

    user_id = session.get('user_id')
    managers = Manager.query.all()
    super_distributors = SuperDistributor.query.all()
    distributors = Distributor.query.all()
    kitchens = Kitchen.query.all()

    # Check if the user is authenticated
    if current_user.is_authenticated:
        # Query the admin by current_user.id if authenticated
        admin = Admin.query.get(current_user.id)
        
        # Encode the image to Base64 for rendering in HTML
        encoded_image = None
        if admin and admin.image:
            encoded_image = b64encode(admin.image).decode('utf-8')
    else:
        # Redirect to login page if the user is not authenticated
        return redirect(url_for('admin_bp.login'))

    return render_template('admin/admin_index.html',
                           manager_count=manager_count,
                           super_distributor_count=super_distributor_count,
                           distributor_count=distributor_count,
                           kitchen_count=kitchen_count,
                           total_sales_amount=total_sales_amount,
                           total_orders_count=total_orders_count,
                           managers=managers, 
                           super_distributors=super_distributors, 
                           distributors=distributors, 
                           kitchens=kitchens,
                           user_name=user_name,
                           admin_username=current_user.name,
                           online_status=admin.online_status if admin else False,
                           role=role)

@socketio.on('custom_event')
def handle_custom_event(data):
    print(f"Received data: {data}")
    emit('response_event', {'message': 'Success'})

def register_signals(app):
    @user_logged_in.connect_via(app)
    def update_online_status_on_login(sender, user):
        if isinstance(user, Admin):
            user.online_status = True
            db.session.commit()

    @user_logged_out.connect_via(app)
    def update_online_status_on_logout(sender, user):
        if isinstance(user, Admin):
            user.online_status = False
            db.session.commit()

VALID_ROLES = ["Admin", "Manager", "SuperDistributor", "Distributor", "Kitchen"]

@admin_bp.route('/add_user/<role>', methods=['GET', 'POST'])
@role_required('Admin')
def add_user(role):
    if role not in VALID_ROLES:
        return jsonify({"error": "Invalid role"}), 400

    if request.method == 'POST':
        data = request.form
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        if password != confirm_password:
            return jsonify({"error": "Passwords do not match"}), 400

        user = create_user(data, role)
        if user:
            return redirect(url_for('admin_bp.admin_dashboard'))
        else:
            return jsonify({"error": "User already exists or invalid role"}), 400

    return render_template('admin/add_user.html', role=role)
    
# Route for Sign Up
@admin_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form
        role = data.get('role')
        if data['password'] != data['confirmPassword']:
            return jsonify({"error": "Passwords do not match"}), 400
         
        user = create_user(data, role)
        if user:
            return render_template('admin/login.html')
        else:
            return jsonify({"error": "User already exists or invalid role"}), 400

    return render_template("admin/signup.html")

# Route for Login 
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            data = request.form
            print("Form Data:", data)  
            
            role = data.get('role')
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return jsonify({"error": "Email and password are required"}), 400
            
            role_model_map = {
                "Admin": Admin,
                "Manager": Manager,
                "SuperDistributor": SuperDistributor,
                "Distributor": Distributor,
                "Kitchen": Kitchen
            }
            
            model = role_model_map.get(role)
            if not model:
                return jsonify({"error": "Invalid role"}), 400
            
            user = model.query.filter_by(email=email).first()

            if not user:
                return jsonify({"error": f"No {role} found with this email."}), 404
            
            if not check_password_hash(user.password, password):
                return jsonify({"error": f"Incorrect password for {role}."}), 401
            
            session['user_id'] = user.id
            session['role'] = role
            session['user_name'] = f"{user.name}" if hasattr(user, 'name') else user.name
            print(user.name)
            # print(session)

            dashboard_routes = {
                "Admin": "admin_bp.admin_dashboard",
                "Manager": "manager.manager_dashboard",
                "SuperDistributor": "super_distributor.super_distributor",
                "Distributor": "distributor.distributor_home",
                "Kitchen": "kitchen.kitchen_dashboard"
            }
            route_name = dashboard_routes.get(role)
            
            if not route_name:
                return jsonify({"error": "Dashboard route not defined for this role"}), 500
            
            return redirect(url_for(route_name))
        
        return render_template('admin/admin.html')

    except Exception as e:
        return handle_error(e)

@admin_bp.route('/manager', methods=['GET'])
@role_required('Manager')  
def manager_dashboard():
    from models import SuperDistributor, Distributor, Kitchen
    super_distributors = SuperDistributor.query.all()
    distributors = Distributor.query.all()
    kitchens = Kitchen.query.all()

    return render_template('admin/manager_dashboard.html', 
                           super_distributors=super_distributors, 
                           distributors=distributors, 
                           kitchens=kitchens)


@admin_bp.route('/super_distributor', methods=['GET'])
@role_required('SuperDistributor')  
def super_distributor_dashboard():
    from models import Distributor, Kitchen
    distributors = Distributor.query.all()
    kitchens = Kitchen.query.all()

    return render_template('admin/super_distributor_dashboard.html', 
                           distributors=distributors, 
                           kitchens=kitchens)


@admin_bp.route('/distributor', methods=['GET'])
@role_required('Distributor')  
def distributor_dashboard():
    from models import Kitchen
    kitchens = Kitchen.query.all()

    return render_template('admin/distributor_dashboard.html', 
                           kitchens=kitchens)


@admin_bp.route('/kitchen', methods=['GET'])
@role_required('Kitchen')  
def kitchen_dashboard():
    from models import Kitchen
    kitchens = Kitchen.query.filter_by(id=session['user_id']).all()  

    return render_template('admin/kitchen_dashboard.html', kitchens=kitchens)

# Route for Logout
@admin_bp.route('/logout')
# @role_required('Admin')
def logout():
    session.pop('user_id', None)
    session.pop('role', None) 
    return render_template('admin/login.html')

# Route for profile of the manager
@admin_bp.route('/admin/<int:admin_id>', methods=['GET'])
def get_admin_profile(admin_id):
    role = session.get('role')

    # Query the admin by id
    admin = Admin.query.get_or_404(admin_id)

    # Encode the image to Base64 for rendering in HTML
    encoded_image = None
    if admin.image:
        encoded_image = b64encode(admin.image).decode('utf-8')

    return render_template('admin/admin_profile.html', admin=admin, role=role, encoded_image=encoded_image)

@admin_bp.route('/edit/<int:admin_id>', methods=['GET', 'POST'])
def edit_admin(admin_id):
    admin = Admin.query.get_or_404(admin_id)

    role = session.get('role')
    user_name = session.get('user_name')

    if isinstance(role, bytes):
        role = role.decode('utf-8')
    if isinstance(user_name, bytes):
        user_name = user_name.decode('utf-8')

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        contact = request.form.get('contact')
        password = request.form.get('password')
        image = request.files.get('image')  # Get the image from the form if provided

        # Validate if email already exists (excluding the current manager)
        existing_admin_email = Admin.query.filter(Admin.email == email, admin.id != admin.id).first()
        if existing_admin_email:
            flash("The email is already in use by another admin.", "danger")
            return render_template('admin/edit_admin.html',admin=admin, role=role, user_name=user_name)

        # Validate if contact already exists (excluding the current manager)
        existing_admin_contact = Admin.query.filter(Admin.contact == contact, Admin.id != admin.id).first()
        if existing_admin_contact:
            flash("The contact number is already in use by another admin.", "danger")
            return render_template('admin/edit_admin.html', admin=admin, role=role, user_name=user_name)

        # Update manager details
        admin.name = name
        admin.email = email
        admin.contact = contact

        # If password is provided, hash and update it
        if password:
            admin.password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Handle image update if a new image is uploaded
        if image and allowed_file(image.filename):
            # Convert the image to binary data
            image_binary = image.read()
            admin.image = image_binary

        try:
            db.session.commit()
            flash("Admin updated successfully!", "success")
            return redirect(url_for('admin_bp.admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating admin: {str(e)}", "danger")

    return render_template('admin/edit_admin.html', admin=admin, role=role, user_name=user_name)


############ Sales Data Visualization ################
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
    total_sales_amount = query.with_entities(db.func.sum(Sales.total_price)).scalar() or 0
    quantity_sold = query.with_entities(db.func.sum(Sales.quantity)).scalar() or 0

    # Total orders count
    total_orders_count = Order.query.count()

    # Get sales data for the line chart (sales by date)
    sales_by_date = db.session.query(
        func.date(Sales.datetime).label('sale_date'),
        func.sum(Sales.total_price).label('total_sales')
    ).filter(Sales.datetime >= start_time, Sales.datetime < end_time).group_by(func.date(Sales.datetime)).all()

    # Process sales data into a dictionary
    sales_by_date_dict = defaultdict(float)
    for sale in sales_by_date:
        sales_by_date_dict[sale.sale_date] += float(sale.total_sales)

    # Convert the sales data (for table and chart)
    dates = [str(date) for date in sales_by_date_dict.keys()] if sales_by_date_dict else ["No Data"]
    sales = list(sales_by_date_dict.values()) if sales_by_date_dict else [0]

    sales_data = query.all()

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

######################## Orders data visualization API ###################################

orders_bp = Blueprint('orders', __name__, url_prefix='/sales')

@orders_bp.route('/list', methods=['GET'])
def order_list():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '', type=str)

    query = Order.query.options(
        joinedload(Order.customer),
        joinedload(Order.order_items).joinedload(OrderItem.food_item)
    )

    if search_query:
        orders = Order.query.join(Customer).filter(
            (Order.order_id.like(f'%{search_query}%')) |
            (Customer.name.like(f'%{search_query}%'))
        ).paginate(page=page, per_page=10)
    else:
        orders = Order.query.paginate(page=page, per_page=10)

    for order in orders.items:
        print(f"Order ID: {order.order_id}")
        if order.order_items:
            for item in order.order_items:
                print(f" - Food Item: {item.food_item.item_name}, Quantity: {item.quantity}")
            else:
                print(" - No order items found")

    return render_template('admin/order_list.html', orders=orders)



######################## Updating User Status ############################
""" from flask_login import current_user, login_required
import logging


socketio = SocketIO()

def get_current_user_id():
    # Placeholder function to fetch the current user ID from the session or token
    # Replace with actual logic based on your authentication implementation
    return current_user.id if current_user.is_authenticated else None

def update_user_status(id, is_online):
    #Update the user's online status in the database.
    if id:
        user = Admin.query.get(id)
        if user:
            user.online_status = is_online
            db.session.commit()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def broadcast_user_status(user_id, is_online):
    #Broadcast user status to all connected clients.
    socketio.emit('user_status_update', {'userId': user_id, 'online': is_online})

@socketio.on('connect')
def handle_connect():
    user_id = get_current_user_id()
    update_user_status(user_id, True)
    broadcast_user_status(user_id, True)
    logger.info(f"User {user_id} connected and marked as online")

@socketio.on('disconnect')
def handle_disconnect():
    user_id = get_current_user_id()
    update_user_status(user_id, False)
    broadcast_user_status(user_id, False)
    print(f"User {user_id} disconnected and marked as offline.") 
    
    """
