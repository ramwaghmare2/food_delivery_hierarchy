from models import db, Admin, Manager, SuperDistributor, Distributor, Kitchen, Sales, Order, Customer, FoodItem
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.services import allowed_file, get_image
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from utils.helpers import handle_error 
from sqlalchemy.orm import joinedload
from collections import defaultdict
from models.order import OrderItem
from extensions import bcrypt
from base64 import b64encode
from functools import wraps
from sqlalchemy import func
# from app import app
admin_bp = Blueprint('admin_bp', __name__, static_folder='../static')

################################## Helper function to create a user based on role ##################################
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

################################## Route for signup ##################################
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


################################## Route for Login ##################################
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
            if user:
                user.online_status = True
                db.session.commit()

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


################################## Logout Route  ##################################
@admin_bp.route('/logout')
def logout():
    try:
        # Retrieve user information from session
        user_id = session.get('user_id')
        role = session.get('role')

        # Map roles to their respective models
        role_model_map = {
            "Admin": Admin,
            "Manager": Manager,
            "SuperDistributor": SuperDistributor,
            "Distributor": Distributor,
            "Kitchen": Kitchen
        }

        model = role_model_map.get(role)

        # If the role and user_id are valid, update online_status
        if model and user_id:
            user = model.query.get(user_id)
            if user:
                user.online_status = False
                db.session.commit()

        # Clear the session
        session.pop('user_id', None)
        session.pop('role', None)

        return redirect(url_for('admin_bp.login'))
    except Exception as e:
        flash(f"Error during logout: {str(e)}", "danger")
        return redirect(url_for('admin_bp.login'))

"""    
################################## Add User Role ##################################
VALID_ROLES = ["Admin", "Manager", "SuperDistributor", "Distributor", "Kitchen"]

@admin_bp.route('/add_user/<role>', methods=['GET', 'POST'])
@role_required('Admin')
def admin_dashboard():
    # Fetch session data
    user_name = session.get('user_name', 'User')
    role = session.get('role')
    user_id = session.get('user_id')

    # Initialize counts and totals
    manager_count = 0
    super_distributor_count = 0
    distributor_count = 0
    kitchen_count = 0
    total_sales_amount = 0
    total_orders_count = 0
    quantity_sold = 0
    try:
        # Fetch data from database
        managers = Manager.query.all()
        manager_count = len(managers)

        super_distributors = SuperDistributor.query.all()
        super_distributor_count = len(super_distributors)

        distributors = Distributor.query.all()
        distributor_count = len(distributors)

        kitchens = Kitchen.query.all()
        kitchen_count = len(kitchens)

        query = Order.query
        #total_sales = Sales.query.all()
        total_sales_amount = query.with_entities(db.func.sum(Order.total_amount)).scalar() or 0

        total_orders = OrderItem.query.all()
        total_orders_count = len(total_orders)
        total_orders = query.with_entities(db.func.sum(OrderItem.quantity)).scalar() or 0

        quantity_sold = Sales.query.all()
        quantity = len(quantity_sold)
        quantity_sold = query.with_entities(db.func.sum(OrderItem.quantity)).scalar() or 0


        print(f"Managers: {manager_count}, Super Distributors: {super_distributor_count}, Distributors: {distributor_count}, Kitchens: {kitchen_count}")
        print(f"Total Sales Amount: {total_sales_amount}, Total Orders Count: {total_orders_count}")

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
        user_name=user_name,
        role=role,
    )
   
"""
################################## Route for displaying admin dashboard ##################################
@admin_bp.route('/admin', methods=['GET'])
@role_required('Admin')
def admin_dashboard():
    # Fetch session data
    user_name = session.get('user_name', 'User')
    role = session.get('role')
    user_id = session.get('user_id')

    # Initialize counts, totals, and sales data
    manager_count = 0
    super_distributor_count = 0
    distributor_count = 0
    kitchen_count = 0
    total_sales_amount = 0
    total_orders_count = 0
    quantity_sold = 0
    sales_data = []

    try:
        # Fetch data from database
        managers = Manager.query.all()
        manager_count = len(managers)

        super_distributors = SuperDistributor.query.all()
        super_distributor_count = len(super_distributors)

        distributors = Distributor.query.all()
        distributor_count = len(distributors)

        kitchens = Kitchen.query.all()
        kitchen_count = len(kitchens)

        total_sales_amount = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0
        total_orders_count = OrderItem.query.count()

        quantity_sold = db.session.query(db.func.sum(OrderItem.quantity)).scalar() or 0

        # Fetch sales data
        sales_data = db.session.query(
            Sales.sale_id,
            Sales.datetime,
            FoodItem.item_name,
            OrderItem.price,
            OrderItem.quantity
        ).join(OrderItem, Sales.item_id == OrderItem.item_id)\
        .join(FoodItem, Sales.item_id == FoodItem.id)\
        .order_by(Sales.datetime.desc())\
        .all()

        print(f"Managers: {manager_count}, Super Distributors: {super_distributor_count}, Distributors: {distributor_count}, Kitchens: {kitchen_count}")
        print(f"Total Sales Amount: {total_sales_amount}, Total Orders Count: {total_orders_count}")
        print(f"Sales Data: {sales_data}")

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
        user_name=user_name,
        role=role,
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
        Sales.sale_id.label('sale_id'),
        Sales.datetime,
        FoodItem.item_name,
        OrderItem.price,
        OrderItem.quantity,
    ).join(OrderItem, FoodItem.id == OrderItem.item_id).all()

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

################################## Manager Dashboard ##################################
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


################################## Super Distributor Bashboard ##################################
@admin_bp.route('/super_distributor', methods=['GET'])
@role_required('SuperDistributor')  
def super_distributor_dashboard():
    from models import Distributor, Kitchen
    distributors = Distributor.query.all()
    kitchens = Kitchen.query.all()

    return render_template('admin/super_distributor_dashboard.html', 
                           distributors=distributors, 
                           kitchens=kitchens)

################################## Distributor Dashboard ##################################
@admin_bp.route('/distributor', methods=['GET'])
@role_required('Distributor')  
def distributor_dashboard():
    from models import Kitchen
    kitchens = Kitchen.query.all()

    return render_template('admin/distributor_dashboard.html', 
                           kitchens=kitchens)

################################## Kitchen Dashboard ##################################
@admin_bp.route('/kitchen', methods=['GET'])
@role_required('Kitchen')  
def kitchen_dashboard():
    from models import Kitchen
    kitchens = Kitchen.query.filter_by(id=session['user_id']).all()  

    return render_template('admin/kitchen_dashboard.html', kitchens=kitchens)


################################## Get All Manager Profile ##################################
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

################################## Edit Admin ##################################
@admin_bp.route('/edit/<int:admin_id>', methods=['GET', 'POST'])
def edit_admin(admin_id):
    admin = Admin.query.get_or_404(admin_id)

    role = session.get('role')
    user_name = session.get('user_name')

    image_data= get_image(role, admin_id)

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

        return render_template('admin/edit_admin.html', admin=admin, role=role, user_name=user_name ,encoded_image=image_data)

    return render_template('admin/edit_admin.html', admin=admin, role=role, user_name=user_name)

