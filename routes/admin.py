from models import db, Admin, Manager, SuperDistributor, Distributor, Kitchen, Sales, Order, Customer, FoodItem
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import emit
from utils.services import allowed_file, get_image, get_user_query
from sqlalchemy.exc import IntegrityError
from utils.helpers import handle_error 
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from models.order import OrderItem
from extensions import bcrypt
from base64 import b64encode
from functools import wraps
from sqlalchemy import func
from app import socketio

admin_bp = Blueprint('admin_bp', __name__, static_folder='../static')

# Sessions permanent with a timeput
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

################################## globally defined role_model_map ##################################

ROLE_MODEL_MAP = {
    "Admin": Admin,
    "Manager": Manager,
    "SuperDistributor": SuperDistributor,
    "Distributor": Distributor,
    "Kitchen": Kitchen,
}

def get_model_by_role(role):
    return ROLE_MODEL_MAP.get(role)

################################## Handel Connect Disconnect ##################################
@socketio.on('connect')
def handle_connect():
    try:
        user_id = session.get('user_id')
        role = session.get('role')

        if user_id and role:
            # The globally defined role_model_map
            model = ROLE_MODEL_MAP(role)
            if model:
                user = model.query.get(user_id)
                if user:
                    user.online_status = True
                    user.last_seen = datetime.now(timezone.utc)
                    db.session.commit()

                    # Notify all connected clients
                    socketio.emit(
                        'status_update',
                        {'user_id': user.id, 
                         'status': 'online', 
                         'role': role,
                         'laste_seen': user.last_seen.isoformat()
                         },
                        broadcast=True
                    )
    except Exception as e:
        print(f"Error in handle_connect: {str(e)}")


@socketio.on('disconnect')
def handle_disconnect():
    reasone = request.args.get('reason', 'unknown')
    print(f"User disconnected due to:{reasone}")
    try:
        user_id = session.get('user_id')
        role = session.get('role')

        if user_id and role:
            model = ROLE_MODEL_MAP(role)
            if model:
                user = model.query.get(user_id)
                if user:
                    user.online_status = False
                    user.last_seen = datetime.now(timezone.utc)
                    db.session.commit()

                    socketio.emit(
                        'status_update',
                        {'user_id': user.id, 
                         'status': 'offline', 
                         'role': role,
                         'laste_seen': user.last_seen.isoformat()
                         },
                        broadcast=True
                    )
        else:
            print("Session data missing on disconnect.")
    except Exception as e:
        print(f"Error in handle_disconnect: {str(e)}")

@admin_bp.route('/update-status', methods=['POST'])
def update_status():
    try:
        data = request.get_json()
        status = data.get('status')
        user_id = session.get('user_id')
        role = session.get('role')

        if user_id and role and status:
            model = ROLE_MODEL_MAP(role)
            if model:
                user = model.query.get(user_id)
                if user:
                    user.online_status = (status == 'online')
                    user.last_seen = datetime.now(timezone.utc)
                    db.session.commit()
        return jsonify({"message": "Status updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
            
            model = ROLE_MODEL_MAP.get(role)
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
            user.online_status = True
            user.last_seen = datetime.now(timezone.utc)
            db.session.commit()

            current_app.socketio.emit(
                'status_update',
                {'user_id': user.id, 
                 'status': 'online', 
                 'role': role,
                 'laste_seen': user.last_seen.isoformat()
                 },
                to='*/'  # Broadcast to all connected clients
            )

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

        model = ROLE_MODEL_MAP.get(role)

        # If the role and user_id are valid, update online_status
        if model and user_id:
            user = model.query.get(user_id)
            if user:
                user.online_status = False
                user.last_seen = datetime.now(timezone.utc)
                db.session.commit()

                # Emit status_update event for logout using socketio
                current_app.socketio.emit(
                    'status_update',
                    {'user_id': user.id, 
                     'status': 'offline', 
                     'role': role,
                     'laste_seen': user.last_seen.isoformat()
                     },
                    to='*/' 
                )

        # Clear the session
        session.clear()

        return redirect(url_for('admin_bp.login'))
    except Exception as e:
        flash(f"Error during logout: {str(e)}", "danger")
        return redirect(url_for('admin_bp.login'))
    

################################## Route for displaying admin dashboard ##################################
@admin_bp.route('/admin', methods=['GET'])
@role_required('Admin')
def admin_dashboard():
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
    monthly_sales = 0

    # chart data initial values
    months = []
    total_sales = []

    barChartData = {
        "labels": ["January", "February", "March", "April"],
        "values": [10, 20, 15, 30],
    }

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

        monthly_sales = db.session.query(
            func.date_trunc('month', Sales.datetime).label('month'),
            func.sum(Order.total_amount).label('total_sales')
        ).join(Order, Sales.sale_id == Order.order_id).group_by(func.date_trunc('month', Sales.datetime)).order_by(func.date_trunc('month', Sales.datetime)).all()
        
        if not barChartData or not isinstance(barChartData, dict):
            barChartData = {}

        months = [month.strftime('%Y-%m') for month, total_sales in monthly_sales]
        total_sales = [float(total_sales) for _, total_sales in monthly_sales]

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

################################## Get All Manager Profile ##################################
@admin_bp.route('/profile', methods=['GET'])
def get_profile():
    role = session.get('role')
    user_id = session.get('user_id')
    # user_name = session.get('user_name')

    role_model_map = {
                "Admin": Admin,
                "Manager": Manager,
                "SuperDistributor": SuperDistributor,
                "Distributor": Distributor,
                "Kitchen": Kitchen
            }
            
    model = role_model_map.get(role)
    
    user = model.query.filter_by(id=user_id).first()

    # Encode the image to Base64 for rendering in HTML
    encoded_image = None
    if user.image:
        encoded_image = b64encode(user.image).decode('utf-8')



    return render_template('admin/user_profile.html', 
                           user=user, 
                           role=role, 
                           encoded_image=encoded_image,
                           user_name=user.name,
                           user_id=user_id,
                           )

################################## Edit Admin ##################################
@admin_bp.route('/profile-edit', methods=['GET', 'POST'])
def edit_profile():

    user_id = session.get('user_id')
    role = session.get('role')
    user = get_user_query(role, user_id)
    encoded_image = get_image(role, user_id)
    role_model_map = {
                "Admin": Admin,
                "Manager": Manager,
                "SuperDistributor": SuperDistributor,
                "Distributor": Distributor,
                "Kitchen": Kitchen
            }
            
    model = role_model_map.get(role)
    
    user = model.query.filter_by(id=user_id).first()
    

    image_data= get_image(role, user_id)

    if isinstance(role, bytes):
        role = role.decode('utf-8')

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        contact = request.form.get('contact')
        password = request.form.get('password')
        image = request.files.get('image')  # Get the image from the form if provided

        # Validate if email already exists (excluding the current manager)
        existing_email = model.query.filter(model.email == email, model.id != user.id).first()
        if existing_email:
            flash(f"The email is already in use by another {role}.", "danger")
            return redirect(url_for('admin_bp.edit_profile'))

        # Validate if contact already exists (excluding the current manager)
        existing_contact = model.query.filter(model.contact == contact, model.id != user.id).first()
        if existing_contact:
            flash(f"The contact number is already in use by another {role}.", "danger")
            return redirect(url_for('admin_bp.edit_profile'))

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
            flash(f"{role} updated successfully!", "success")
            return redirect(url_for('admin_bp.get_profile'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating {role}: {str(e)}", "danger")
            return redirect(url_for('admin_bp.edit_profile'))

    return render_template('admin/edit_profile.html', 
                           user=user, 
                           role=role, 
                           user_name=user.name,
                           user_id=user_id,
                           encoded_image=encoded_image
                           )

