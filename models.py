from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

from image import createImage
from faker import Faker


fake = Faker()

db = SQLAlchemy()
# To create db run: flask shell Then from app import db Then db.create_all() Then you leave withexit with bracket

user_friend = db.Table('user_friend', 
    db.Column("friend_id", db.Integer, db.ForeignKey('users.id'), primary_key=True, nullable=False),
    db.Column("user_id", db.Integer, db.ForeignKey('users.id'), primary_key=True, nullable=False),
)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    about = db.Column(db.String(500), nullable=True, default='Hey there, I am using Vinochat')
    email = db.Column(db.String(100), nullable=False, unique=True)
    image = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(50), nullable=False)
    reg_date = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)

    # self-referential many-to-many relationship
    friends = db.relationship("User",
        secondary = user_friend,
        primaryjoin = (id == user_friend.c.user_id),
        secondaryjoin = (id == user_friend.c.friend_id),
        backref = "friend_of",
    )

    # friends = db.relationship('Friend', backref='user')
    # messages = db.relationship('Message', backref='user')
    posts = db.relationship('Post', backref='user')

user_post = db.Table('user_post', 
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True)
)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    friend_id = db.Column(db.Integer, nullable=False)
    # friend_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    attachement = db.Column(db.String(100), nullable=True)
    message = db.Column(db.String(500), nullable=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=True)
    image = db.Column(db.String(50), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)

def add_users():
    for _ in range(250):
        names = fake.name()
        user = User(
            name = names,
            email = fake.email(),
            password = generate_password_hash('12345'),
            image = createImage(names) 
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