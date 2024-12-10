from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from models import SuperDistributor, Distributor, Kitchen, Order, Sales, OrderItem, FoodItem
from utils.services import get_model_counts ,allowed_file ,get_image, get_user_query
from werkzeug.security import generate_password_hash
from models.manager import db, Manager
from extensions import bcrypt
from base64 import b64encode
from flask import Blueprint


manager_bp = Blueprint('manager', __name__,template_folder='../templates/manager', static_folder='../static')

# Route to Add a new manager
@manager_bp.route('/add', methods=['GET', 'POST'])
def add_manager():

    role = session.get('role')                 # Get the role from  the session
    user_name = session.get('user_name') 
    user_id = session.get('user_id')
    image_data= get_image(role, user_id)       
    user = get_user_query(role, user_id)
    if request.method == 'POST':
        name = request.form['name']     # Get the name from  the form
        email = request.form['email']   # Get the email from  the form
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')  # Hash password
        contact = request.form.get('contact')   # Get the contact from the form
        image = request.files.get('image')  # Get the image from the form

        image_binary = None
        if image and allowed_file(image.filename):
            image_binary = image.read()

        # Check if the email is already in use
        existing_email = Manager.query.filter_by(email=email).first()
        if existing_email:
            flash("Error: Email is already in use.", "danger")
            return render_template('add_manager.html',role=role, user_name=user_name)

        # Check if the contact number is already in use
        existing_contact = Manager.query.filter_by(contact=contact).first()
        if existing_contact:
            flash("Error: Contact number is already in use.", "danger")
            return render_template('add_manager.html',role=role, user_name=user_name)

        # Create manager instance and add to database
        new_manager = Manager(name=name, 
                        email=email, 
                        password=password, 
                        contact=contact,
                        image=image_binary)
        try:
            db.session.add(new_manager)
            db.session.commit()
            flash("Manager added successfully!", "success")
            return redirect(url_for('manager.add_manager'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding manager: {str(e)}", "danger")
    
    return render_template('add_manager.html', role=role,user_name=user_name, encoded_image = image_data)


@manager_bp.route('/managers', methods=['GET'])
def get_managers():
    role = session.get('role')
    user_name = session.get('user_name')
    user_id = session.get('user_id')
    image_data = get_image(role, user_id)  # Fetch user image
    counts = get_model_counts()  # Fetch model counts (e.g., for dashboard stats)
    user = get_user_query(role, user_id)
    # Get filter status from request parameters
    filter_status = request.args.get('status', 'all').lower()

    try:
        # Decode role and user_name if they are bytes
        role = role.decode('utf-8') if isinstance(role, bytes) else role
        # user_name = user_name.decode('utf-8') if isinstance(user_name, bytes) else user_name

        # Fetch managers based on filter
        if filter_status == 'activated':
            managers = Manager.query.filter_by(status='activated').all()
        elif filter_status == 'deactivated':
            managers = Manager.query.filter_by(status='deactivated').all()
        else:  # 'all' or no filter
            managers = Manager.query.all()

        # Convert images to Base64 format for rendering
        for manager in managers:
            if manager.image:
                manager.image_base64 = f"data:image/jpeg;base64,{b64encode(manager.image).decode('utf-8')}"
            else:
                manager.image_base64 = None

        # Render the template with filtered managers
        return render_template(
            'managers.html',
            managers=managers,
            role=role,
            user_name=user.name,
            filter=filter_status,  # Pass the filter to the template
            **counts,
            encoded_image=image_data
        )
    except Exception as e:
        flash(f"Error retrieving managers: {str(e)}", "danger")
        return render_template(
            'managers.html',
            managers=[],
            role=role,
            user_name=user.name,
            filter=filter_status,
            **counts,
            encoded_image=image_data
        )

# Route for edit the manager
@manager_bp.route('/edit/<int:manager_id>', methods=['GET', 'POST'])
def edit_manager(manager_id):
    manager = Manager.query.get_or_404(manager_id)
    user_id = session.get('user_id')
    role = session.get('role')
    image_data = get_image(role, user_id)
    user = get_user_query(role, user_id)

    if isinstance(role, bytes):
        role = role.decode('utf-8')
    # if isinstance(user_name, bytes):
    #     user_name = user_name.decode('utf-8')

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        contact = request.form.get('contact')
        password = request.form.get('password')
        image = request.files.get('image')  # Get the image from the form if provided

        # Validate if email already exists (excluding the current manager)
        existing_manager_email = Manager.query.filter(Manager.email == email, Manager.id != manager.id).first()
        if existing_manager_email:
            flash("The email is already in use by another manager.", "danger")
            return render_template('edit_manager.html', manager=manager, role=role, user_name=user.name,encoded_image=image_data)

        # Validate if contact already exists (excluding the current manager)
        existing_manager_contact = Manager.query.filter(Manager.contact == contact, Manager.id != manager.id).first()
        if existing_manager_contact:
            flash("The contact number is already in use by another manager.", "danger")
            return render_template('edit_manager.html', manager=manager, role=role, user_name=user.name,encoded_image=image_data)

        # Update manager details
        manager.name = name
        manager.email = email
        manager.contact = contact

        # If password is provided, hash and update it
        if password:
            manager.password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Handle image update if a new image is uploaded
        if image and allowed_file(image.filename):
            # Convert the image to binary data
            image_binary = image.read()
            manager.image = image_binary

        try:
            db.session.commit()
            flash("Manager updated successfully!", "success")
            return redirect(url_for('manager.get_managers'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating manager: {str(e)}", "danger")

    return render_template('edit_manager.html', manager=manager, role=role, user_name=user.name,encoded_image=image_data)


# Route for delete the manager
@manager_bp.route('/delete/<int:manager_id>', methods=['GET', 'POST'])
def delete_manager(manager_id):
    manager = Manager.query.get_or_404(manager_id)

    try:
        manager.status = 'deactivated'
        # db.session.delete(manager)
        db.session.commit()
        flash("Manager deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting manager: {str(e)}", "danger")

    return redirect(url_for('manager.get_managers'))


# Route for profile of the manager
@manager_bp.route('/manager/<int:manager_id>', methods=['GET'])
def get_manager_profile(manager_id):
    try:
        # Query the manager by id
        manager = Manager.query.get_or_404(manager_id)

        return render_template('manager_profile.html', manager=manager)

    except Exception as e:
        flash(f"Error retrieving manager profile: {str(e)}", "danger")
        return redirect(url_for('manager.get_managers'))


@manager_bp.route('/', methods=['GET', 'POST'], endpoint='manager_dashboard')
def manager_dashboard():
    # Fetch session data
    user_name = session.get('user_name', 'User')
    role = session.get('role')
    user_id = session.get('user_id')

    # Initialize counts, totals, and sales data
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
        super_distributors = SuperDistributor.query.filter_by(manager_id=user_id).all()
        super_distributor_ids = [sd.id for sd in super_distributors]
        super_distributor_count = len(super_distributors)

        distributors = Distributor.query.filter(Distributor.super_distributor.in_(super_distributor_ids)).all()
        distributor_ids = [dist.id for dist in distributors]
        distributor_count = len(distributor_ids)

        all_kitchens = Kitchen.query.filter(Kitchen.distributor_id.in_(distributor_ids)).all()
        kitchen_ids = [kitchen.id for kitchen in all_kitchens]
        kitchen_count = len(all_kitchens)

        total_sales_amount = db.session.query(db.func.sum(Order.total_amount)).filter(Order.kitchen_id == user_id).scalar() or 0

        total_orders_count = db.session.query(OrderItem).join(Order).filter(Order.kitchen_id == user_id).count()

        quantity_sold = db.session.query(db.func.sum(OrderItem.quantity)).join(Order).filter(Order.kitchen_id == user_id).scalar() or 0

        sales_data = (
            db.session.query(
                Sales.sale_id,
                Sales.datetime,
                FoodItem.item_name,
                db.func.sum(OrderItem.price).label("total_price"),
                db.func.sum(OrderItem.quantity).label("total_quantity"),
            )
            .join(OrderItem, Sales.item_id == OrderItem.item_id)
            .join(FoodItem, OrderItem.item_id == FoodItem.id)
            .join(Order, OrderItem.order_id == Order.id)
            .filter(Order.manager_id == user_id)
            .group_by(Sales.sale_id, FoodItem.item_name, Sales.datetime)
            .order_by(Sales.datetime.desc())
            .all()
        )

        monthly_sales = (
            db.session.query(
                db.func.date_format(Sales.datetime, '%Y-%m').label('month'),
                db.func.sum(Order.total_amount).label('total_sales'),
            )
            .join(Order, Sales.sale_id == Order.order_id)
            .filter(Order.manager_id == user_id)
            .group_by(db.func.date_format(Sales.datetime, '%Y-%m'))
            .order_by(db.func.date_format(Sales.datetime, '%Y-%m'))
            .all()
        )

        months = [month for month, _ in monthly_sales]
        total_sales = [float(total) for _, total in monthly_sales]
    except Exception as e:
        print(f"Error fetching data: {e}")

    # Render the manager dashboard template
    return render_template(
        'manager/manager_index.html',
        super_distributor_count=super_distributor_count,
        distributor_count=distributor_count,
        kitchen_count=kitchen_count,
        total_sales_amount=total_sales_amount,
        total_orders_count=total_orders_count,
        quantity_sold=quantity_sold,
        sales_data=sales_data,
        user_name=user_name,
        role=role,
        months=months,
        total_sales=total_sales,
        barChartData=barChartData,
    )
