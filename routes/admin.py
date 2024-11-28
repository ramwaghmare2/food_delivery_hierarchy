from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash, current_app
from flask_socketio import SocketIO, emit
# from flask_login import user_logged_in, user_logged_out, current_user
# from flask_security.signals import user_logged_in, user_logged_out
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from models import db, Admin, Manager, SuperDistributor, Distributor, Kitchen, Sales, Order, Customer
from models.order import OrderItem
from utils.helpers import handle_error 
from utils.services import allowed_file ,get_model_counts ,get_image
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from base64 import b64encode
from extensions import bcrypt, socketio
from datetime import datetime, timedelta
from collections import defaultdict

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
    # Fetch session data
    user_name = session.get('user_name', 'User')
    role = session.get('role')
    user_id = session.get('user_id')
    counts = get_model_counts()
    image_data = get_image(role, user_id)
    user = Admin.query.get_or_404(user_id)

    # Initialize counts and data variables
    count = {}
    admin = None
    admin_username = "Guest"
    online_status = False
    managers, super_distributors, distributors, kitchens = [], [], [], []
    total_sales_amount = 0
    total_orders_count = 0

    if current_user.is_authenticated:
        # Fetch authenticated user's admin data
        admin = Admin.query.get(current_user.id)
        admin_username = current_user.user_name if admin else "Admin"
        online_status = admin.online_status if admin else False

        # Update the online status of the current admin
        if admin:
            admin.online_status = True  # Mark as online
            admin.last_active = datetime.utcnow()  # Update last active timestamp
            db.session.commit()

        # Get counts for entities
        
        managers = Manager.query.all()
        super_distributors = SuperDistributor.query.all()
        distributors = Distributor.query.all()
        kitchens = Kitchen.query.all()

        # Query sales and orders data
        total_sales = Sales.query.all()
        total_orders = Order.query.all()
        total_sales_amount = sum(sale.price for sale in total_sales)
        total_orders_count = len(total_orders)

        # Fetch admin image data
        #image_data = get_image(role, current_user.id)
    #else:
        # Fetch image data only if user_id is available
        #image_data = get_image(role, user_id) if user_id else None

    # Handle inactive status based on a timeout (e.g., 5 minutes of inactivity)
    if admin and admin.last_active:
        now = datetime.utcnow()
        if now - admin.last_active > timedelta(minutes=5):
            admin.online_status = False  # Mark as offline after timeout
            db.session.commit()

    # Render the admin dashboard template
    return render_template(
        'admin/admin_index.html',
        **counts,
        user=user,
        encoded_image=image_data,
        managers=managers,
        super_distributors=super_distributors,
        distributors=distributors,
        kitchens=kitchens,
        user_name=user_name,
        admin_username=admin_username,
        total_sales_amount=total_sales_amount,
        total_orders_count=total_orders_count,
        online_status=online_status,
        role=role,
    )



"""@socketio.on('custom_event')
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
"""
            
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

            if role == 'Admin':
                pass
            elif user.status == 'deactivated' or user.status == '':
                flash('User is not Active', 'danger')
                return redirect(url_for('admin_bp.login'))

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
        
        return render_template('admin/login.html')

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
@admin_bp.route('/admin/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    role = session.get('role')

    # Query the admin by id
    user = Admin.query.get_or_404(user_id)

    # Encode the image to Base64 for rendering in HTML
    encoded_image = None
    if user.image:
        encoded_image = b64encode(user.image).decode('utf-8')

    return render_template('admin/admin_profile.html', user=user, user_name=user.name, role=role, encoded_image=encoded_image)

@admin_bp.route('/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_admin(user_id):
    user = Admin.query.get_or_404(user_id)

    role = session.get('role')
    user_name = session.get('user_name')

    image_data= get_image(role, user_id)

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
        existing_admin_email = Admin.query.filter(Admin.email == email, user.id != user.id).first()
        if existing_admin_email:
            flash("The email is already in use by another admin.", "danger")
            return render_template('admin/edit_admin.html',user=user, role=role, user_name=user_name)

        # Validate if contact already exists (excluding the current manager)
        existing_admin_contact = Admin.query.filter(Admin.contact == contact, user.id != user.id).first()
        if existing_admin_contact:
            flash("The contact number is already in use by another admin.", "danger")
            return render_template('admin/edit_admin.html', user=user, role=role, user_name=user_name)

        # Update manager details
        user.name = name
        user.email = email
        user.contact = contact

        # If password is provided, hash and update it
        if password:
            user.password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Handle image update if a new image is uploaded
        if image and allowed_file(image.filename):
            # Convert the image to binary data
            image_binary = image.read()
            user.image = image_binary

        try:
            db.session.commit()
            flash("Admin updated successfully!", "success")
            return redirect(url_for('admin_bp.get_user_profile',user_id=user_id,user_name=user_name))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating admin: {str(e)}", "danger")

        return render_template('admin/edit_admin.html', user=user, role=role, user_name=user_name ,encoded_image=image_data)

    return render_template('admin/edit_admin.html', user=user, role=role, user_name=user_name ,encoded_image=image_data)


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


