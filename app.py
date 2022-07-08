import email
from gevent import monkey
monkey.patch_all()
from flask_socketio import SocketIO
from email import message
import os
from email.policy import default
import mimetypes
from re import sub
from unittest import result
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
#from flask_mail import Mail, Message
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from models import User, Message, user_friend

from helpers import login_required, user_image
from image import createImage

from models import db

UPLOAD_FOLDER = 'static/images/users'
ALLOWED_EXTENSIONS = set(['png', 'jpeg', 'jpg'])

app = Flask("__name__")
# socketio for server to client event
app.config['SECRET_KEY'] = 'itsyoursecret!'
socketio = SocketIO(app)

# Profile Images Upload Folder
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'

# Custom filter
app.jinja_env.filters["user_image"] = user_image

# Requires that "Less secure app access" be on
# https://support.google.com/accounts/answer/6010255
app.config["MAIL_DEFAULT_SENDER"] = "os.environ['MAIL_DEFAULT_SENDER']"
app.config["MAIL_PASSWORD"] = "os.environ['MAIL_PASSWORD']"
app.config["MAIL_PORT"] = 587
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "os.environ['MAIL_USERNAME']"
#mail = Mail(app)


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db.init_app(app) # add line after all app config.

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

#db = SQLAlchemy(app)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id 
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

        name = request.form.get("name").strip()
        email = request.form.get("email")
        password = request.form.get("password")
        cpassword = request.form.get("cpassword")

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
        if User.query.filter_by(email=email).first():
            flash("Email already exist!" )
            return render_template("register.html")

        image = createImage(name)

        # create user
        user = User(name=name, email=email, image=image, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()

        #message = Message("Registration completed successfully!", recipients=[email])
        #mail.send(message)

        # redirect to login and show message
        error = "Awesome, you have been registered! Please Login"
        return render_template("login.html", error=error)

    else:
        return render_template("register.html")


@app.route('/', methods = ['GET'])
@login_required
def index():
    id = session['user_id']
    user = User.query.filter_by(id=id).first()
    session_friend = session.get('friend_id', id)
    friend = User.query.filter_by(id=session_friend).first()
    
    if user is None:
        return redirect("/login")

    messages = Message.query.filter(Message.user_id.like(user.id), Message.friend_id.like(id), Message.friend_id.like(friend.id)).all()

    subq = db.session.query(user_friend).filter(user_friend.c.friend_id == id).subquery()
    thefriends = User.query.join(subq, User.id == subq.c.user_id).all()
    ourfriends = []
    for afriend in user.friends:
        ourfriends.append(afriend.id)
    for ufriend in thefriends:
        ourfriends.append(ufriend.id)
    allfriends = User.query.filter(User.id.in_(ourfriends))
    page = request.args.get('page', 1, type=int)
    get_potential_friends = User.query.filter(~User.id.in_(ourfriends))
    records = get_potential_friends.paginate(page=page, per_page=20)
    if "hx_request" in request.headers:
        return render_template("record.html", datas = records)
    return render_template('index.html', **locals())

@app.route("/add-friend")
def addFriend():
    page = request.args.get('page', 1, type=int)
    add_users = User.query.paginate(page=page, per_page=50)
    return render_template("record.html", datas = add_users)

def sendNewFriendMessage(user_id, friend_id):
    query = Message(user_id=user_id, friend_id=friend_id, send_id=friend_id)
    db.session.add(query)
    db.session.commit()

@app.route('/new-friend', methods=['POST'])
def newFriend():
    if session.get("user_id") is None:
        return redirect("/login")

    id = session['user_id']
    friend_id = request.form.get("friend_id")

    if not friend_id:
        return "Error: User not found!"

    """myfriends = db.session.query(User).filter_by(id=id).all()
    temp = []
    for myfriend in myfriends:
        element = myfriend.friend_id
        temp.append(element)

    a = set(temp)
    n = int(friend_id)
    if n in a:
        return ("Error: You are friends already")"""

    friend = User.query.filter_by(id=friend_id).first()
    user = User.query.filter_by(id=id).first()
    sendNewFriendMessage(id, friend_id)
    loadData()
    user.friends.append(friend)
    db.session.commit()
    return "success"

@app.route('/search', methods=['POST'])
def search():
    search = request.form.get('search', None)
    if search:
        users = User.query.filter(User.name.like(f'%{search}%')).all()
        return render_template('search.html', results=users)
    id = session['user_id']
    user = User.query.filter_by(id=id).first()
    
    if user is None:
        return redirect("/login")

    subq = db.session.query(user_friend).filter(user_friend.c.friend_id == id).subquery()
    thefriends = User.query.join(subq, User.id == subq.c.user_id).all()
    ourfriends = []
    for afriend in user.friends:
        ourfriends.append(afriend.id)
    for ufriend in thefriends:
        ourfriends.append(ufriend.id)
    allfriends = User.query.filter(User.id.in_(ourfriends))
    return render_template('search.html', results=allfriends)

@app.route('/search-all', methods=['POST'])
def searchall():
    search = request.form.get('searchall', None)
    if search:
        users = User.query.filter(User.name.like(f'%{search}%')).all()
        return render_template('allsearch.html', results=users)
    id = session['user_id']
    user = User.query.filter_by(id=id).first()
    
    if user is None:
        return redirect("/login")

    subq = db.session.query(user_friend).filter(user_friend.c.friend_id == id).subquery()
    thefriends = User.query.join(subq, User.id == subq.c.user_id).all()
    ourfriends = []
    for afriend in user.friends:
        ourfriends.append(afriend.id)
    for ufriend in thefriends:
        ourfriends.append(ufriend.id)
    allfriends = User.query.filter(User.id.in_(ourfriends))
    return render_template('allsearch.html', results=allfriends)


@app.route('/retrieve-message', methods=['GET'])
def retrieveMessage():
    user_id = session['user_id']
    friend_id = session.get('friend_id', id)
    messages = Message.query.filter(db.or_(db.and_(Message.user_id.like(user_id), Message.friend_id.like(friend_id)), db.and_(Message.friend_id.like(user_id), Message.user_id.like(friend_id))))
    if messages:
        return render_template('messages.html', messages=messages)

@app.route('/retrieve-friend', methods=['GET'])
def retrieveFriend():
    friend_id = session.get('friend_id', id)
    friend = User.query.filter_by(id=friend_id).first()
    return render_template('fhead.html', friend=friend)

@app.route('/retrieve-user', methods=['GET'])
def retrieveUser():
    id = session['user_id']
    user = User.query.filter_by(id=id).first()
    return render_template('loaduser.html', user=user)

@app.route('/retrieve-user-image', methods=['GET'])
def retrieveUserImage():
    id = session['user_id']
    user = User.query.filter_by(id=id).first()
    return render_template('userimage.html', user=user)

@app.route('/get-message', methods=['POST'])
def getMessage():
    user_id = session['user_id']
    session['friend_id'] = None
    friend_id = request.form.get("friend_id")
    if not friend_id:
        flash("User not found!")
        return redirect("/")
    messages = Message.query.filter(db.or_(db.and_(Message.user_id.like(user_id), Message.friend_id.like(friend_id)), db.and_(Message.friend_id.like(user_id), Message.user_id.like(friend_id)))).group_by(Message.date)

    session['friend_id'] = int(friend_id)
    query = db.session.query(Message).filter(db.and_(Message.friend_id.like(user_id), Message.user_id.like(friend_id))).all()
    for c in query:
        c.views = 1
    db.session.commit()
    #return jsonify(messages)
    return render_template('messages.html', messages=messages)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/send-message', methods=['POST'])
def sendMessage():
    user_id = session['user_id']
    friend_id = session['friend_id']
    message = request.form.get("message")

    if not message and 'file' not in request.files:
        return render_template('form.html')      

    if 'file' in request.files:
        file = request.files['file']

        if file.filename == '':
            return "No file selected"
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
    else:
        filename = None

    query = Message(user_id=user_id, friend_id=friend_id, send_id=user_id, message=message, attachement=filename) 
    db.session.add(query)
    db.session.commit()
    messages = Message.query.filter(db.or_(db.and_(Message.user_id.like(user_id), Message.friend_id.like(friend_id)), db.and_(Message.friend_id.like(user_id), Message.user_id.like(friend_id))))
    loadData()
    return render_template('form.html', messages=messages)

@app.route('/all-user-message', methods=['GET'])
def getAllUserMessage():
    id = session['user_id']

    friends = db.session.query(Message).filter(db.or_(Message.friend_id.like(id), Message.user_id.like(id))).group_by(Message.send_id).order_by(db.desc(Message.date), db.func.max(Message.date)).all()

    return render_template('friends.html', friends=friends)

@app.route('/update-profile', methods=['POST'])
def updateProfile():
    id = session['user_id']
    name = request.form.get("name")
    about = request.form.get("about")
    
    if not name:
        return f"<span style='color:red'>Name cannot be empty!</span>"

    elif not about:
        return ("<span style='color:red'>About cannot be empty!</span>")
    
    user = User.query.filter_by(id=id).first()
    
    if 'file' in request.files:
        
        file = request.files['file']

        if file.filename == '':
            return ("No file selected")
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
    else:
        filename = user.image
    
    user.name = name
    user.about = about
    user.image = filename
    db.session.commit()
    loadData()

    return "<span style='color:green'>Profile Updated</span>"


@app.route('/check-count', methods=['POST'])
def checkCount():
    id = session["user_id"]
    friend_id = int(request.form.get("count"))
    count = db.session.query(db.func.count(Message.id)).filter(db.and_(Message.friend_id.like(id), Message.user_id.like(friend_id))).filter(Message.views==0).scalar()
    return render_template("count.html", count=count)

@app.route('/contact-info', methods=['GET'])
def contactInfo():
    session_friend = session['friend_id']
    friend = User.query.filter_by(id=session_friend).first()
    return render_template('contact.html', friend=friend)

@socketio.on('message')
def handle_message(data):
    print(data)

def loadData():
    print("Data updated")
    socketio.emit('dataUpdated', {'data': 42})

def showCount():
    print("Count updated")
    socketio.emit('updateCount', {'data': 42})

@app.route('/delete-message', methods=['POST'])
def deleteMessage():
    messageId = request.form.get("messageId")
    if messageId:
        query = Message.query.filter_by(id=messageId).one()
    db.session.delete(query)
    db.session.commit()
    loadData()
    return render_template('form.html')

@app.route('/<name>/<email>')
def gjsk(name, location):
    user = User(name=name, email=email)
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

if __name__ == '__main__':
    socketio.run(app)