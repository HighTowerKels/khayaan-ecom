from flask import Flask, flash, render_template, request, redirect, url_for, jsonify, abort, Response, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy
import sqlite3
from flask_login import UserMixin, LoginManager, login_required, login_user, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, FloatField, SelectField
from wtforms.validators import InputRequired, Length, NumberRange, ValidationError
from wtforms.validators import Email
from flask_migrate import Migrate
from wtforms.validators import InputRequired, Length, Email 
from flask_mail import Mail
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename
import re
from datetime import datetime, time, timedelta
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from sqlalchemy.orm import relationship
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_bcrypt import Bcrypt, bcrypt

app = Flask(__name__, static_url_path='/static')
basedir = os.path.abspath(os.path.dirname((__file__)))
database = "app.db"
con = sqlite3.connect(os.path.join(basedir, database))
mail = Mail(app)
app.config['SECRET_KEY'] = "jhkxhiuydu"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, database)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
app.config['MAIL_SERVER'] = 'intexcoin.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'info@intexcoin.com'
app.config['MAIL_SERVER'] = 'server148.web-hosting.com'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.add_url_rule('/static/uploads/<filename>', 'uploads', build_only=True)
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(255)  )

    email = db.Column(db.String(255), unique=True, nullable=True)
    password = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(100), nullable=True)  # Making user_location nullable
   
    phone_number = db.Column(db.String(20), nullable=True)  # Making phone_number nullable
    phone_number_two = db.Column(db.String(20), nullable=True)
    
    last_login_at = db.Column(db.DateTime, default=datetime.utcnow)



    is_admin = db.Column(db.Boolean, default=False)
    profile_picture = db.Column(db.String(255))  # Add profile picture column


    def check_password(self, password):
        return check_password_hash(self.password, password)

    def set_password(self, password):
        self.password = generate_password_hash(password)
    def create(self, fullname='', location='', email='', password='', phone_number = ''):
        self.fullname = fullname
        self.location = location
        self.email = email
        self.phone_number = phone_number
        self.password = generate_password_hash(password, method='sha256')
    
    def is_profile_updated(self):
        # Check if all mandatory fields are filled
        required_fields = [self.location, self.fullname, self.phone_number, self.email]
        return all(required_fields)

        # Optionally, check if specific optional fields are filled
        # For example, check if the second phone number is filled
        # if not self.second_phone_number:
        #     return False

        # # Optionally, check if uploaded documents are valid
        # # For example, check if the NIN photo exists
        # if not os.path.exists(self.nin_photo):
        #     return False
    
    
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    def commit(self):
        db.session.commit()   
    def get_id(self):
        return str(self.id)

class Product(db.Model):
    __tablename__ = 'product'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.String(100), nullable=False)
    currency = db.Column(db.String(20), nullable=False)
    product_type = db.Column(db.String(50), nullable=False)
    image1 = db.Column(db.String(100))  # Assuming the filename is stored in the database
    image2 = db.Column(db.String(100))
    image3 = db.Column(db.String(100))

    def __init__(self, name, description, price, currency, product_type):
        self.name = name
        self.description = description
        self.price = price
        self.currency = currency
        self.product_type = product_type

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_ordered = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    customer_id = db.Column(db.Integer, nullable=False)  # Reference to user/customer model
    status = db.Column(db.String(20), nullable=False, default='Pending')
    order_items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    product = db.relationship('Product', backref='order_items')

class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # Reference to the user model
    wishlist_items = db.relationship('WishlistItem', backref='wishlist', lazy=True)

class WishlistItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wishlist_id = db.Column(db.Integer, db.ForeignKey('wishlist.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product')




@app.route('/')
@app.route('/home')
def index():
    essential_products = Product.query.filter_by(product_type='Essentials').all()
    skin_products = Product.query.filter_by(product_type='Skin').all()
    return render_template('index.html', skin_products = skin_products, essential_products = essential_products)

@app.route('/categories')
def category():
    return render_template('categories.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', title='Login')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        location = request.form.get('location')
        phone_number = request.form.get('phone_number')
        phone_number_two = request.form.get('phone_number_two')
        
        if not fullname or not email or not password or not confirm_password:
            flash('Please fill out all required fields.', 'danger')
        elif password != confirm_password:
            flash('Passwords do not match.', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Email is already registered.', 'danger')
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            user = User(fullname=fullname, email=email, password=hashed_password,
                        location=location, phone_number=phone_number, phone_number_two=phone_number_two)
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', title='Register')


@app.route('/cart')
def cart():
    cart_items = session.get('cart', {})
    total_price = sum(float(item['price'].replace(',', '')) * item['quantity'] for item in cart_items.values())
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@app.route('/cart/add/<int:product_id>', methods=['POST', 'GET'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    cart = session.get('cart', {})

    if str(product_id) in cart:
        cart[str(product_id)]['quantity'] += 1
    else:
        cart[str(product_id)] = {
            'name': product.name,
            'price': product.price.replace(',', ''),  # Remove comma before converting to float
            'quantity': 1
        }

    session['cart'] = cart
    flash(f'Added {product.name} to cart', 'success')
    return redirect(url_for('view_products'))



@app.route('/cart/update/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    quantity = int(request.form.get('quantity'))
    cart = session.get('cart', {})

    if str(product_id) in cart:
        if quantity > 0:
            cart[str(product_id)]['quantity'] = quantity
        else:
            del cart[str(product_id)]

    session['cart'] = cart
    flash('Cart updated', 'success')
    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart = session.get('cart', {})

    if str(product_id) in cart:
        del cart[str(product_id)]

    session['cart'] = cart
    flash('Product removed from cart', 'success')
    return redirect(url_for('cart'))


# @app.route("/product/new", methods=['GET', 'POST'])
# def new_product():
#     if request.method == 'POST':
#         name = request.form.get('name')
#         description = request.form.get('description')
#         price = request.form.get('price')
#         stock = request.form.get('stock')
#         product = Product(name=name, description=description, price=float(price), stock=int(stock))
#         db.session.add(product)
#         db.session.commit()
#         flash('Product created successfully!', 'success')
#         return redirect(url_for('view_products'))
#     return render_template('create_product.html')

@app.route('/products')
def view_products():
    products = Product.query.all()
    return render_template('products.html', products=products)


@app.route('/products/<int:product_id>')
def product_details(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('pro-details.html', product=product)

@app.route("/product/<int:product_id>/update", methods=['GET', 'POST'])
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price'))
        product.stock = int(request.form.get('stock'))
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('product_detail', product_id=product.id))
    return render_template('update_product.html', product=product)

@app.route("/product/<int:product_id>/delete", methods=['POST'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('view_products'))


@app.route('/order', methods=['GET', 'POST'])
def create_order():
    if request.method == 'POST':
        customer_id = current_user.id  # Assuming user authentication is set up
        cart = session.get('cart', {})

        if not cart:
            flash('Your cart is empty!', 'danger')
            return redirect(url_for('view_products'))

        order = Order(customer_id=customer_id, status='Pending')
        db.session.add(order)
        db.session.commit()

        for product_id, item in cart.items():
            order_item = OrderItem(order_id=order.id, product_id=product_id, quantity=item['quantity'])
            db.session.add(order_item)

        db.session.commit()
        session['cart'] = {}  # Clear the cart after order is placed
        flash('Order has been placed successfully!', 'success')
        return redirect(url_for('view_orders'))

    return render_template('create_order.html')

@app.route('/orders')
def view_orders():
    orders = Order.query.filter_by(customer_id=current_user.id).all()  # Assuming user authentication is set up
    return render_template('view_orders.html', orders=orders)

@app.route('/order/<int:order_id>')
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.customer_id != current_user.id:
        flash('You are not authorized to view this order.', 'danger')
        return redirect(url_for('view_orders'))
    return render_template('order_detail.html', order=order)

@app.route('/wishlist')
def view_wishlist():
    wishlist = Wishlist.query.filter_by(user_id=current_user.id).first()
    wishlist_items = wishlist.wishlist_items if wishlist else []
    return render_template('view_wishlist.html', wishlist_items=wishlist_items)

@app.route('/wishlist/add/<int:product_id>', methods=['POST'])
def add_to_wishlist(product_id):
    product = Product.query.get_or_404(product_id)
    wishlist = Wishlist.query.filter_by(user_id=current_user.id).first()

    if not wishlist:
        wishlist = Wishlist(user_id=current_user.id)
        db.session.add(wishlist)
        db.session.commit()

    wishlist_item = WishlistItem.query.filter_by(wishlist_id=wishlist.id, product_id=product.id).first()
    
    if wishlist_item:
        flash('Product is already in your wishlist.', 'info')
    else:
        wishlist_item = WishlistItem(wishlist_id=wishlist.id, product_id=product.id)
        db.session.add(wishlist_item)
        db.session.commit()
        flash(f'Added {product.name} to your wishlist.', 'success')
    
    return redirect(url_for('view_products'))

@app.route('/wishlist/remove/<int:product_id>', methods=['POST'])
def remove_from_wishlist(product_id):
    wishlist = Wishlist.query.filter_by(user_id=current_user.id).first()
    if wishlist:
        wishlist_item = WishlistItem.query.filter_by(wishlist_id=wishlist.id, product_id=product_id).first()
        if wishlist_item:
            db.session.delete(wishlist_item)
            db.session.commit()
            flash('Product removed from your wishlist.', 'success')
        else:
            flash('Product not found in your wishlist.', 'danger')
    return redirect(url_for('view_wishlist'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/nav')
def nav():
    return render_template('nav.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')
@app.route('/faq')
def faq():
    return render_template('faq.html')
@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/process',methods=['GET','POST'])


def process():
    auths = User()
    if request.method == "POST":
        
        password = request.form['password']
        email = request.form['email']
        auths = User(
             password=password,email=email,is_admin=True)
        db.session.add(auths)
        db.session.commit()
        return "welcome sign up completed"
    return render_template('admin_signup.html')


@app.route('/signin',methods=['GET','POST'])
def signin():
    user = User()
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['passwords']
        user = User.query.filter_by(email=email,is_admin=True).first()
       
        if user:
            if user.password == password:
                login_user(user)
                return redirect('dashboard')

                
                
            


    return render_template('admin_login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')
    

@app.route('/transaction')
def transaction():
    
    return render_template('transaction.html')

@app.route('/sales')
def sales():
    return render_template('sale.html')

@app.route('/product/create' , methods=['GET','POST'])
def product():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price =request.form.get('price')
        currency = request.form.get('currency')
        product_type = request.form.get('productType')

        # Handle file uploads
        image_files = []
        for i in range(1, 4):
            file = request.files.get(f'image{i}')
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_files.append(filename)

        # Create the product instance
        product = Product(name=name, description=description, price=price, currency=currency, product_type=product_type)

        # Assuming you have an attribute in your Product model to store image filenames
        product.image1 = image_files[0] if len(image_files) >= 1 else None
        product.image2 = image_files[1] if len(image_files) >= 2 else None
        product.image3 = image_files[2] if len(image_files) >= 3 else None

        db.session.add(product)
        db.session.commit()
        flash('Product created successfully!', 'success')
       
    return render_template('create_products.html')

@app.route('/members')
def members():
    return render_template('members.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')


@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route("/db/renew")
def database():
    db.drop_all()
    db.create_all()
    return "Hello done!!!"

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5500, debug=True)

