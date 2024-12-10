from flask import Blueprint, render_template, request, url_for, redirect, flash, session
from models import Manager, SuperDistributor, Distributor, Kitchen, Sales, Order
from werkzeug.security import generate_password_hash
from models import db
import bcrypt
from utils.services import get_model_counts ,allowed_file, get_image, get_user_query
from base64 import b64encode
from sqlalchemy import func
from datetime import datetime, timedelta


super_distributor_bp = Blueprint('super_distributor', __name__, template_folder='../templates/super_distributor', static_folder='../static')

################################## Route for Super Distributor Dashboard ##################################
@super_distributor_bp.route('/super-distributor', methods=['GET'])
def super_distributor():
    role = session.get('role')
    user_id = session.get('user_id')
    image_data= get_image(role, user_id) 
    user = get_user_query(role, user_id)
    # Initialize counts and totals
    distributor_count = 0
    kitchen_count = 0
    total_sales_amount = 0
    total_orders_count = 0

    try:
        distributors = Distributor.query.filter_by(super_distributor=user_id).all()
        distributor_count = len(distributors)

        distributor_ids = [distributor.id for distributor in distributors]
        kitchens = Kitchen.query.filter(Kitchen.distributor_id.in_(distributor_ids)).all()
        kitchen_count = len(kitchens)

        orders = Order.query.filter(Order.kitchen_id.in_([kitchen.id for kitchen in kitchens])).all()
        total_orders_count = len(orders)

        
        total_sales_amount = db.session.query(func.sum(Order.total_amount)).filter(
                                Order.kitchen_id.in_([kitchen.id for kitchen in kitchens])
                            ).scalar() or 0
        
        # Filter sales by kitchen_id
        sales = Sales.query.filter(Sales.kitchen_id.in_([kitchen.id for kitchen in kitchens])).all()
        # total_orders_count = len(sales)  # Total number of orders (sales records)
        total_quantity_sold = 0

        # Loop through each sale to calculate total sales amount and quantity sold
        for sale in sales:
            # total_sales_amount += sale.orders.total_amount  # Assuming `total_amount` is the sale's total amount
            for item in sale.orders.order_items:  # Assuming there's an order_items relationship
                total_quantity_sold += item.quantity

        # Aggregate order counts and sales by date (daily)
        order_dates = []
        sales_per_date = []
        order_count_per_date = []

        # Aggregating data by day
        for days_offset in range(30):  # For the last 30 days
            date = datetime.now() - timedelta(days=days_offset)
            formatted_date = date.strftime('%Y-%m-%d')
            order_dates.append(formatted_date)
            
            # Count orders and sales for the specific date
            orders_on_date = Order.query.filter(Order.kitchen_id == user_id, func.date(Order.created_at) == date.date()).all()
            order_count_per_date.append(len(orders_on_date))

            sales_on_date = db.session.query(func.sum(Order.total_amount)).filter(Order.kitchen_id == user_id, func.date(Order.created_at) == date.date()).scalar()
            sales_per_date.append(float(sales_on_date) if sales_on_date else 0)
        


    except Exception as e:
        print(f"Error fetching data: {e}")


    return render_template('sd_index.html',
                           user_id=user_id,
                           user_name=user.name,
                           role=role,
                           sales=sales,
                           encoded_image = image_data,
                           distributor_count=distributor_count,
                           kitchen_count=kitchen_count,
                           total_sales_amount=total_sales_amount,
                           total_orders_count=total_orders_count,
                           total_quantity_sold=total_quantity_sold,
                           sales_per_date=sales_per_date,
                           order_count_per_date=order_count_per_date,
                           order_dates=order_dates,
                           )

################################## Route for Get All Super Distributor's ##################################
@super_distributor_bp.route('/all-super-distributor', methods=['GET'])
def all_super_distributor():
    role = session.get('role')
    user_id = session.get('user_id')
    image_data = get_image(role, user_id)
    counts = get_model_counts()
    user = get_user_query(role, user_id)

    # Get filter status from request parameters
    filter_status = request.args.get('status', 'all').lower()

    # Base query
    if role == 'Admin':
        query = SuperDistributor.query
    else:
        query = SuperDistributor.query.filter_by(manager_id=user_id)

    # Apply filter based on status
    if filter_status == 'activated':
        query = query.filter_by(status='activated')
    elif filter_status == 'deactivated':
        query = query.filter_by(status='deactivated')

    # Fetch the filtered super distributors
    all_super_distributors = query.all()

    # Convert images to Base64 format
    for sd in all_super_distributors:
        if sd.image:
            sd.image_base64 = f"data:image/jpeg;base64,{b64encode(sd.image).decode('utf-8')}"
        else:
            sd.image_base64 = None

    return render_template(
        'sd_all_distributor.html',
        all_super_distributors=all_super_distributors,
        role=role,
        user_name=user.name,
        **counts,
        encoded_image=image_data,
        filter=filter_status,
    )
    
################################## Route for Ass Distributor ##################################
@super_distributor_bp.route('/add-distributor', methods=['GET', 'POST'])
def add_distributor():
    role = session.get('role')
    user_id = session.get('user_id')
    image_data= get_image(role, user_id) 
    user = get_user_query(role, user_id)
    try:

        super_distributors = SuperDistributor.query.all() 


        if request.method == 'POST':
            image = request.files.get('image')
            print(image)
            if role== "SuperDistributor":
                super_distributor = session.get('user_id')
            else:
                super_distributor = request.form.get('super_distributor')

            image_binary = None
            if image and allowed_file(image.filename):
                image_binary = image.read()

            if Distributor.query.filter_by(email=request.form.get('email')).first() or Distributor.query.filter_by(contact=request.form.get('mobile_number')).first():
                flash('Distributor with this email or mobile number already exists.')
                return redirect(url_for('super_distributor.add_distributor'))

            hashed_password = generate_password_hash(request.form.get('password'))

            new_distributor = Distributor(
                name=request.form.get('name'),
                email=request.form.get('email'),
                password=hashed_password,
                contact=request.form.get('mobile_number'),
                super_distributor=super_distributor,
                image=image_binary
            )

            db.session.add(new_distributor)
            db.session.commit()
            flash('Distributor Added Successfully.')
            return redirect(url_for('super_distributor.add_distributor'))

        return render_template('sd_add_distributor.html', 
                               role=role,  
                               super_distributors=super_distributors, 
                               user_name=user.name,
                               encoded_image=image_data,
                               )

    except Exception as e:
        flash(f'Error: {e}')
        return redirect(url_for('super_distributor.add_distributor'))

################################## Add Super Distributor ##################################
@super_distributor_bp.route('/add-super-distributor', methods=['GET', 'POST'])
def add_super_distributor():
    
    role = session.get('role')
    user_id = session.get('user_id')
    image_data= get_image(role, user_id) 
    user = get_user_query(role, user_id)
    try:

        managers = Manager.query.all()

        if request.method == 'POST':
            image = request.files.get('image')

            image_binary = None
            if image and allowed_file(image.filename):
                image_binary = image.read()

            if role== "Admin":
                manager_id = request.form.get('manager')
            else:
                manager_id = session.get('user_id')

            if SuperDistributor.query.filter_by(email=request.form.get('email')).first() or SuperDistributor.query.filter_by(contact=request.form.get('mobile_number')).first():
                flash('Super Distributor with this email or mobile number already exists.')
                return redirect(url_for('super_distributor.add_super_distributor'))

            hashed_password = generate_password_hash(request.form.get('password'))

            new_distributor = SuperDistributor(
                name=request.form.get('name'),
                email=request.form.get('email'),
                password=hashed_password,
                contact=request.form.get('mobile_number'),
                manager_id=manager_id,
                image=image_binary
            )

            db.session.add(new_distributor)
            db.session.commit()
            flash('Super Distributor Added Successfully.')
            return redirect(url_for('super_distributor.add_super_distributor'))

        return render_template('add_super_distributor.html', role=role,managers=managers, user_name=user.name, encoded_image = image_data)

    except Exception as e:
        flash(f'Error: {e}')
        return redirect(url_for('super_distributor.add_distributor'))


################################## Function for edit the super_distributor ##################################
@super_distributor_bp.route('/edit/<int:sd_id>', methods=['GET', 'POST'])
def edit_super_distributor(sd_id):
    role = session.get('role')
    user_id = session.get('user_id')
    image_data= get_image(role, user_id) 
    sd = SuperDistributor.query.get_or_404(sd_id)

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        contact = request.form.get('contact')
        password = request.form['password']
        image = request.files.get('image')  # Get the image from the form if it exists

        # Validate if email already exists (excluding the current manager)
        existing_manager_email = SuperDistributor.query.filter(SuperDistributor.email == email, SuperDistributor.id != SuperDistributor.id).first()
        if existing_manager_email:
            flash("The email is already in use by another Super Distributor.", "danger")
            return render_template('edit_super_distributor.html', super_distributor=sd, role=role , user_name=sd.name)

        # Validate if contact already exists (excluding the current manager)
        existing_manager_contact = SuperDistributor.query.filter(SuperDistributor.contact == contact, SuperDistributor.id != SuperDistributor.id).first()
        if existing_manager_contact:
            flash("The contact number is already in use by another Super Distributor.", "danger")
            return render_template('edit_super_distributor.html', super_distributor=sd, role=role, user_name=sd.name)

        # Update manager details
        sd.name = name
        sd.email = email
        sd.contact = contact

        # If password is provided, hash and update it
        if password:
            sd.password = bcrypt.generate_password_hash(password).decode('utf-8')

        if image and allowed_file(image.filename):
            # Convert the image to binary data
            image_binary = image.read()
            sd.image = image_binary

        try:
            db.session.commit()
            flash("Super Distributor updated successfully!", "success")
            return redirect(url_for('super_distributor.all_super_distributor'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating Super Distributor: {str(e)}", "danger")
            return render_template('edit_super_distributor.html', super_distributor=sd, role=role ,user_name=sd.name, encoded_image=image_data)

    return render_template('edit_super_distributor.html', super_distributor=sd, role=role ,user_name=sd.name, encoded_image = image_data)


################################## Function for delete the super distributor ##################################
@super_distributor_bp.route('/delete/<int:sd_id>', methods=['GET', 'POST'])
def delete_super_distributor(sd_id):
    super_distributor = SuperDistributor.query.get_or_404(sd_id)

    try:
        super_distributor.status = 'deactivated'
        # db.session.delete(super_distributor)
        db.session.commit()
        flash("Super Distributor deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting manager: {str(e)}", "danger")

    return redirect(url_for('super_distributor.all_super_distributor'))


@super_distributor_bp.route('/sd-orders', methods=['GET'])
def super_distributors_orders():
    try:
        user_id = session.get('user_id')
        role = session.get('role')

        # Get filter order status from request parameters
        order_status = request.args.get('status', 'all')


        # Apply filter for order status if it's not 'all'
        if order_status != 'All':
            query_filter = query_filter.filter(Order.order_status.ilike(order_status))  # Case-insensitive filter

        super_distributor = SuperDistributor.query.filter_by(id=user_id).first()
        if super_distributor:
            distributor_ids = [distributor.id for distributor in super_distributor.distributors]
            kitchens = Kitchen.query.filter(Kitchen.distributor_id.in_(distributor_ids)).all()
            kitchen_ids = [kitchen.id for kitchen in kitchens]
            if kitchen_ids:
                orders = query_filter.filter(Order.kitchen_id.in_(kitchen_ids)).all()
        
        # Prepare orders data for display
        orders_data = [
            {
                'order_id': order.order_id,
                'kitchen_id': order.kitchen_id,
                'kitchen_name': order.kitchen.name,
                'total_amount': order.total_amount,
                'status': order.order_status,
                'created_at': order.created_at,
                'updated_at': order.updated_at,
                'items': [
                    {
                        'item_id': item.food_item.item_name,
                        'quantity': item.quantity,
                        'price': item.food_item.price,
                        'item_total_price': item.price,
                        'total_price': item.price * item.quantity
                    }
                    for item in order.order_items
                ]
            }
            for order in orders
        ]
        
        return render_template('sd_orders.html',
                               role=role,
                               orders_data=orders_data,
                               
                               )

    except Exception as e:
        flash({'error': str(e)})
        if role == 'SuperDistributor':
            return redirect(url_for('super_distributor.super_distributor'))
