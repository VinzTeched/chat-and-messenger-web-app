from datetime import datetime, timedelta
from email.policy import default
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
import random

from helpers import apology, login_required
from faker import Faker

fake = Faker()

app = Flask("__name__")
# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# To create db run: flask shell Then from app import db Then db.create_all() Then you leave withexit with bracket

db = SQLAlchemy(app)

class User(db.Model):
    #__tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    about = db.Column(db.String(500), nullable=True, default='Hey there, I am using Vinochat')
    email = db.Column(db.String(100), nullable=False, unique=True)
    image = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(50), nullable=False)
    reg_date = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)

    friends = db.relationship('Friend', backref='user')
    messages = db.relationship('Message', backref='user')

user_post = db.Table('user_post', 
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True)
)

class Friend(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    # one to many relationship to customers
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    attachement = db.Column(db.String(100), nullable=True)
    message = db.Column(db.String(500), nullable=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=True)
    image = db.Column(db.String(50), nullable=True)
    date = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)

def add_users():
    for _ in range(30):
        user = User(
            name = fake.name(),
            email = fake.email(),
            password = generate_password_hash('12345') 
        )
        db.session.add(user)
    db.session.commit()


def create_random_data():
    db.create_all()
    add_users()

def get_orders_by(customer_id=1):
    print('Get Orders by Customer')
    customer_orders = Order.query.filter_by(customer_id=customer_id).all()
    for order in customer_orders:
        print(order.customer.first_name)

def get_pending_orders():
    print('Pending Orders')
    pending_orders = Order.query.filter(Order.shipped_date.is_(None)).order_by(Order.order_date.desc()).all()
    for order in pending_orders:
        print(order.order_date)

def how_many_customers():
    print('How many customers?')
    print(Customer.query.count())

def orders_with_code():
    print('Orders with coupon code')
    orders = Order.query.filter(Order.coupon_code.isnot(None)).filter(Order.coupon_code != 'FREESHIPPING').all()
    for order in orders:
        print(order.coupon_code)

def revenue_in_last_x_days(x_days=30):
    print('Revenue past x days')
    query = db.session.query(db.func.sum(Product.price)).join(order_product).join(Order).filter(Order.order_date > (datetime.now() - timedelta(days=x_days))).scalar()
    print(query)

def average_fulfillment_time():
    print('Average Fulfillment Time')
    query = db.session.query(db.func.time(db.func.avg(db.func.strftime('%s', Order.shipped_date) - db.func.strftime('%s', Order.order_date)), 'unixepoch')).filter(Order.shipped_date.isnot(None)).scalar()
    print(query)

def get_customers_who_have_purchased_x_dollars(amount=500):
    print('All Customers who have purchased x dollars')
    customers = db.session.query(Customer).join(Order).join(order_product).join(Product).group_by(Customer).having(db.func.sum(Product.price) > amount).all()
    for customer in customers:
        print(customer.first_name)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id sandraperez@example.com
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        error = None
        # Ensure username was submitted
        if not request.form.get("email"):
            error = "Please provide your email!"
            flash(error)
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            error = "Please provide your password!"
            flash(error)
            return render_template("login.html")

        # Query database for username
        user = User.query.filter_by(email = request.form.get("email")).first()

        # Ensure username exists and password is correct
        if user is None or not check_password_hash(user.password, request.form.get("password")):
            error = "Invalid username and/or password!"
            flash(error)
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = user.id

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        cpassword = request.form.get("confirmation")

        if not name:
            flash("Please provide your name")
            return render_template("register.html")

        if not email:
            flash("Please provide your email")
            return render_template("register.html")

        if not password:
            flash("Please set a password")
            return render_template("register.html")

        if not cpassword:
            flash("Please confirm your password")
            return render_template("register.html")

        if password != cpassword:
            flash("Your password does not match")
            return render_template("register.html")

        #check if user already exists
        stars = db.execute("SELECT * FROM users WHERE username = ?", username)

        if stars:
            return apology("username already exist!", 400)

        # create user
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, generate_password_hash(password))

        # retrieve user
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # call session
        session["user_id"] = rows[0]["id"]

        # show message
        flash("Registered!")

        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/")
@login_required
def index():
    return render_template('index.html')

@app.route('/<name>/<location>')
def gjsk(name, location):
    user = User(name=name, location=location)
    db.session.add(user)
    db.session.commit()

    return '<h1>Added New User</h1>' 

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")