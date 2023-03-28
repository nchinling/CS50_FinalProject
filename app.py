import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from helpers import apology, login_required, lookup, usd

#folder to store images
UPLOAD_FOLDER = 'static/uploads/'

# Configure application
app = Flask(__name__)

#Configurations for uploading images
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


# # Make sure API key is set
# if not os.environ.get("API_KEY"):
#     raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    uid = session["user_id"]
    # userdata = db.execute("SELECT username, lastname, firstname, email, contactnumber FROM users WHERE id = ?", uid)
    listing = db.execute("SELECT listings.item, listings.desc, listings.price, listings.meetup,listings.time,users.username,users.email FROM listings,users WHERE listings.user_id =users.id AND listings.type='available' ORDER by listings.time DESC")
    
    user=db.execute("SELECT username FROM users JOIN listings ON listings.user_id = users.id")

    return render_template("index.html", listing=listing, usd=usd,user=user)


# @app.route("/buy", methods=["GET", "POST"])
# @login_required
# def buy():
#     """Buy shares of stock"""
#     if request.method == "POST":
#         symbol = request.form.get("symbol").upper()
#         stock = lookup(symbol)

#         if not symbol:
#             return apology("Please enter a valid symbol")
#         elif not stock:
#             return apology("Invalid symbol")

#         try:
#             shares = int(request.form.get("shares"))
#         except:
#             return apology("Share quantity must be an integer")

#         if shares <= 0:
#             return apology("Share quantity must be positive")

#         uid = session["user_id"]
#         cash = db.execute("SELECT cash FROM users WHERE id = ?", uid)[0]["cash"]
#         print(f'\n\n{cash}\n\n')

#         stock_name = stock["name"]
#         stock_price = stock["price"]
#         total_price = stock_price * shares

#         if cash < total_price:
#             return apology("You do not have enough cash")
#         else:
#             db.execute("UPDATE users SET CASH = ? WHERE id = ?", cash - total_price, uid)
#             db.execute("INSERT INTO transactions(user_id, name, shares, price, type, symbol) VALUES (?, ?, ?, ?, ?, ?)",
#                        uid, stock_name, shares, stock_price, 'buy', symbol)

#         return redirect('/')

#     else:
#         return render_template("buy.html")


# @app.route("/history")
# @login_required
# def history():
#     """Show history of transactions"""
#     uid = session["user_id"]
#     hist = db.execute("SELECT type, symbol, price, shares, time FROM transactions WHERE user_id = ?", uid)

#     return render_template("history.html", histo=hist, usd=usd)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # to display username at layout page
        session["user"] = rows[0]["username"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if (request.method == "POST"):
        username = request.form.get('username')
        password = request.form.get('password')
        confirmation = request.form.get('confirmation')

        lastname = request.form.get('last_name')
        firstname = request.form.get('first_name')
        email = request.form.get('email')
        contactnumber = request.form.get('contact_number')

        if not username:
            return apology('Please enter username.')
        if not password:
            return apology('Please enter password.')
        if not confirmation:
            return apology('Please confirm password')
        if password != confirmation:
            return apology('Passwords do not match')
        if not (lastname and firstname and contactnumber and email):
            return apology('Please enter all fields correctly')

        hashvalue = generate_password_hash(password)

        try:
            db.execute("INSERT INTO users (username, hash,lastname, firstname, email, contactnumber) VALUES(?,?,?,?,?,?)", username, hashvalue, lastname, firstname, email, contactnumber )
            return redirect('/')
        except:
            return apology('Username has been registered')

    else:
        return render_template("register.html")


@app.route("/list", methods=["GET", "POST"])
@login_required
def list():
    uid = session["user_id"]
    
    # Information for item listed
    if request.method == "POST":
        item = request.form.get("item")
        price = request.form.get("price")
        desc = request.form.get("desc")
        meetup = request.form.get("meetup")

        # available_items = db.execute("SELECT item FROM listings WHERE user_id = ?, uid)[0]["item"]

        # db.execute("UPDATE users SET cash = ? WHERE id = ?", current_cash + sold_amount, uid)
        db.execute("INSERT INTO listings(user_id, type, item, price, desc, meetup) VALUES (?,?,?,?,?,?)",
                   uid, "available", item, price, desc, meetup)
        # return redirect("profile.html")
        userdata = db.execute("SELECT username, lastname, firstname, email, contactnumber FROM users WHERE id = ?", uid)

        listing = db.execute("SELECT item, type, desc, price, meetup FROM listings WHERE user_id = ? ORDER by time DESC", uid)

        return render_template("profile.html", userdata=userdata,listing=listing, usd=usd)
        
        
    else:
        listings = db.execute("SELECT item FROM listings WHERE user_id =?", uid)
        return render_template("list.html", listings=listings)


# Additional feature: profile page where user is able to top up cash


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    # Show profile
    uid = session["user_id"]

    if request.method == "POST":
        return render_template("update_profile.html")

    else:
        userdata = db.execute("SELECT username, lastname, firstname, email, contactnumber FROM users WHERE id = ?", uid)

        listing = db.execute("SELECT id,item, desc, price, meetup,type FROM listings WHERE user_id = ? ORDER by time DESC", uid)

        return render_template("profile.html", userdata=userdata,listing=listing, usd=usd)


@app.route("/update_profile", methods=["GET", "POST"])
@login_required
def update_profile():
    # Show profile
    uid = session["user_id"]

    if request.method == "POST":
        password = request.form.get('new_password')
        confirmation = request.form.get('confirmation')
        email = request.form.get('new_email')
        contactnumber = request.form.get('new_contact_number')

        if not password:
            return apology('Please enter password.')
        if not confirmation:
            return apology('Please confirm password')
        if password != confirmation:
            return apology('Passwords do not match')
        if not (contactnumber and email):
            return apology('Please enter all fields correctly')

        hashvalue = generate_password_hash(password)
        try:
           
            db.execute("UPDATE users SET hash = ?,email = ?, contactnumber =? where id = ?", hashvalue, email, contactnumber,uid )

            return render_template("profile_updated.html")

        except:
            return apology('Error encountered')

    else:
        return render_template("update_profile.html")



@app.route("/sold", methods=["GET", "POST"])
@login_required
def sold():
    # Show profile
  
    uid = session["user_id"]
    # listingid=request.form.getlist("sold")[0]

    if request.method == "POST":
        listingid=request.form.get("sold")
        try:
            db.execute("UPDATE listings SET type = 'sold' WHERE id = ?", listingid)

            return render_template("item_updated.html")

        except:
            return apology('Error encountered')

