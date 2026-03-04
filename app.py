from flask import Flask, render_template, redirect, url_for, request, make_response,flash,session

import jwt
from datetime import datetime, timedelta, timezone
from flask import jsonify

from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename
from database.connection import databaseConfig

# ------------------- Load environment variables ------------------

from dotenv import load_dotenv
import os
import razorpay


# ------------import database logics -------------------
from database.tables import createTables
from database.utility import checkUserExists, addUser, getUserDetails, getCatagoriesFromDB, getProductsFromDB
from database.utility import addProductToDB, totalOrdersCount, getOrders, usersDetails, getUserDetailsByID, updateAdminProfile
from database.utility import getProductDetailsByID, updateProductInfo, updateProductStatus, viewUserByAdmin, totalProductsCount,totalUsersCount,pendingOrdersCount

app = Flask(__name__)
app.config['SECRET_KEY'] = "jawahar@1130"

# load environment variables from .env file
load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

razorpay_client = razorpay.Client(
    auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
)
   



## -------------------------- Helper Functions ------------------------------------


## token protection decorator
def token_required(role=None):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.cookies.get('token')

            if not token:
                return redirect(url_for('login'))

            try:
                data = jwt.decode(
                    token,
                    app.config['SECRET_KEY'],
                    algorithms=["HS256"]
                )
            except jwt.ExpiredSignatureError:
                return redirect(url_for('login'))
            except jwt.InvalidTokenError:
                return redirect(url_for('login'))
            
            request.userid = data['userid']
            request.role = data['role']

            if role and data['role'] != role:
                return "Unauthorized access"

            return f(*args, **kwargs)
        return decorated
    return wrapper


def getUserByToken():
    token = request.cookies.get('token')

    if not token:
        return None

    try:
        data = jwt.decode(
            token,
            app.config['SECRET_KEY'],
            algorithms=["HS256"]
        )

        userid = data.get('userid')
        role = data.get('role')

        user = getUserDetailsByID(userid=userid)

        return user

    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None



# index route
@app.route('/')
def index():
    return render_template('user/user_dashboard.html',
                            user_logged_in=False)


# login route
@app.route("/login", methods=['GET',"POST"])
def login():
    # if it is POST request method
    # get form data
    if request.method == 'POST':
        username = request.form['email']
        password = request.form['password']
       
        # user validation
        data = getUserDetails(email=username)
        print(data)
        if data and check_password_hash(data['password'], password):
            
            # create login token
            # utc_now = datetime.now(timezone.utc)

            # Add 2 hours
            exp_time = datetime.now(timezone.utc) + timedelta(hours=2)

            token = jwt.encode(
                {
                    "userid": data["userid"],
                    "role": data["role"],
                    "exp": exp_time
                },
                app.config['SECRET_KEY'],
                algorithm="HS256"
            )

             # Based on role it selects the user dashbord or admin dashboard
            response = make_response(
                redirect(url_for('admin' if data['role']=='admin' else 'user'))
            )

            # store token in cookie
            response.set_cookie(
                'token',
                token,
                httponly=True,
                secure=False  # True in production (HTTPS)
            )

            return response
        # If credintial is incorrect
        flash('User Credentials incorrect')
        return redirect(url_for('login'))

    # if it is get request 
    return render_template('auth/login.html')



# ---------------------- image upload paths ------------------
PROFILE_UPLOAD_FOLDER = 'static/uploads/profile'
PRODUCT_UPLOAD_FOLDER = 'static/uploads/products'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

app.config['PROFILE_UPLOAD_FOLDER'] = PROFILE_UPLOAD_FOLDER
app.config['PRODUCT_UPLOAD_FOLDER'] = PRODUCT_UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# ------------------------------------------------------------
#registe Route
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        profile_image = request.files.get('profile_image')

        # basic validation
        if not name or not email or not phone or not password:
            flash("All required fields must be filled")
            return redirect(url_for('register'))

        # check user already exists
        if checkUserExists(email=email):
            flash("Email already registered")
            return redirect(url_for('register'))

        # password hash
        hashed_password = generate_password_hash(password)

        # handle profile image
        image_path = None
        if profile_image and profile_image.filename != "":
            if allowed_file(profile_image.filename):
                filename = secure_filename(profile_image.filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

                image_path = os.path.join(
                    app.config['UPLOAD_FOLDER'],
                    filename
                )

                profile_image.save(image_path)
            else:
                flash("Invalid image format")
                return redirect(url_for('register'))

        # add user to database
        addUser(
            name=name,
            email=email,
            phone_number=phone,
            password=hashed_password,
            profile_image=image_path
        )

        flash("Registration successful. Please login.")
        return redirect(url_for('login'))

    return render_template('auth/register.html')


# forgotpassword route
@app.route('/forgotpassword')
def forgotpassword():
    return "forgot Password Page"



## Admin Routes
# admin dashborad route
@app.route('/admin')
@token_required(role='admin')
def admin():

    total_products = totalProductsCount()
    total_orders = totalOrdersCount()
    pending_orders = pendingOrdersCount()
    total_users = totalUsersCount()
    return render_template('admin/dashboard.html',
                            total_products=total_products,
                            total_orders=total_orders,
                            pending_orders=pending_orders,
                            total_users=total_users
                        )

# product route

@app.route('/admin/products')
@token_required(role='admin')
def adminproducts():
    # get all categories name 
    categories = getCatagoriesFromDB()

    product_name = request.args.get('name',"")
    category = request.args.get('category', "")
    status = request.args.get('status', "")

    print(category, product_name, status)
    # Get all products from  database
    products = getProductsFromDB(name=product_name, category= category, status= status)
    #print(products[:3])
    return render_template('admin/products.html', categories= categories, products=products)

# Add product Route

@app.route('/admin/addproduct', methods=['GET','POST'])
@token_required(role='admin')
def adminaddproduct():
    categories = getCatagoriesFromDB()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        category = request.form['category']
        active = request.form['active']
        price = request.form['price']
        stock = request.form['stock']
        image = request.files.get('image')
        new_category = request.form.get('new_category')

        if category == "new":
            if not new_category or new_category.strip() == "":
                flash("Please enter a new category", "danger")
                return redirect(url_for('adminaddproduct'))
            category = new_category.strip()

        image_path = None
        if image and image.filename != "":
            if allowed_file(image.filename):
                filename = secure_filename(image.filename)

                os.makedirs(app.config['PRODUCT_UPLOAD_FOLDER'], exist_ok=True)

                save_path = os.path.join(
                    app.config['PRODUCT_UPLOAD_FOLDER'],
                    filename
                )
                image.save(save_path)

                image_path = f"uploads/products/{filename}"
            else:
                flash("Invalid image format", "danger")
                return redirect(url_for('adminaddproduct'))

        addProductToDB(
            name=name,
            description=description,
            category=category,
            price=price,
            stock=stock,
            active=active,
            image_url=image_path
        )

        flash("Product added successfully", "success")
        return redirect(url_for('adminproducts'))

    return render_template('admin/addproduct.html',
                           categories=categories)


@app.route('/admin/editproduct/<int:productid>', methods=['GET', 'POST'])
@token_required(role='admin')
def editproduct(productid):

    # get product data
    product = getProductDetailsByID(productid=productid)

    # get all categories
    categories = getCatagoriesFromDB()

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        category = request.form.get('category')
        price = request.form.get('price')
        stock = request.form.get('stock')
        active = request.form.get('active')

        if updateProductInfo(name, description, category, price, stock, active, productid):
            flash("Product updated successfully", "success")
            return redirect(url_for('adminproducts'))

        flash("Product NOT updated", "danger")
        return redirect(url_for('adminproducts'))

    return render_template(
        'admin/edit_product.html',
        product=product,
        categories=categories
    )

# deactivate user
# view user 
@app.route('/admin/deactivate_product/<int:productid>', methods=['POST'])
@token_required(role='admin')
def deactivate_product(productid):
    # update in database
    status = updateProductStatus(productid=productid, status=0)
    if status:
        flash("Product deactivated successfully", "warning")
        return redirect(url_for('adminproducts'))
    flash("Product Not deactivated", "Error")
    return redirect(url_for('adminproducts'))
    
@app.route('/admin/activate_product/<int:productid>', methods=['POST'])
@token_required(role='admin')
def activate_product(productid):
    # update in database
    status = updateProductStatus(productid=productid, status=1)
    if status:
        flash("Product Activates successfully", "warning")
        return redirect(url_for('adminproducts'))
    flash("Product Not activated", "Error")
    return redirect(url_for('adminproducts'))
    

@app.route('/admin/users')
@token_required(role='admin')
def adminusers():

    # filters
    name = request.args.get('name', '').strip()
    email = request.args.get('email', '').strip()
    role = request.args.get('role', '').strip()
    users = usersDetails(name=name, email=email, role=role)
    

    return render_template(
        "admin/users.html",
        users=users,
        total_users=len(users)
    )


# orders Route

@app.route('/admin/orders')
@token_required(role='admin')
def adminorders():
    # get filter parameter 
    orderid = request.args.get('orderid',"")
    product_name = request.args.get('productname',"")
    from_date = request.args.get('fromdate',"")
    to_date = request.args.get('todate',"")

    orders_count = totalOrdersCount()
    # getting filtered orders
    orders = getOrders(orderid=orderid,
                       product_name=product_name,
                       from_date=from_date,
                       to_date=to_date)
    filter_orders_count = len(orders)
    # print(orders[:3])

    return render_template('admin/orders.html',
                            total_orders = orders_count,
                            filtered_order_count=filter_orders_count,
                            orders=orders)

# view order details route
@app.route('/admin/order/<int:order_id>')
@token_required(role='admin')
def view_order(order_id):
    orders = getOrders(orderid=order_id)

    if not orders:
        flash("Order not found", "danger")
        return redirect(url_for('adminorders'))

    return render_template(
        'admin/view_order.html',
        order=orders[0]
    )


# view user 
@app.route('/admin/viewuser/<int:userid>', methods=['GET', 'POST'])
@token_required(role='admin')
def view_user(userid):

    # get user data from database
    user = viewUserByAdmin(userid=userid)
    if not user:
        flash("User not found", "danger")
        return redirect(url_for('adminusers'))

    return render_template(
        'admin/view_user.html',
        user=user
    )
    

# deactivate user
# view user 
@app.route('/admin/deactivate/<int:userid>', methods=['GET', 'POST'])
@token_required(role='admin')
def deactivate_user(userid):
    return "deactivate user"


# admin profile route

@app.route('/admin/profile', methods=['GET', 'POST'])
@token_required(role='admin')
def adminprofile():

    user = getUserByToken()   # helper → decodes token, returns user data

    if request.method == 'POST':

        name = request.form.get('name')
        phone = request.form.get('phone')

        updateAdminProfile(
            userid=user['userid'],
            name=name,
            phone=phone
        )

        flash("Profile updated successfully", "success")
        return redirect(url_for('adminprofile'))

    return render_template(
        'admin/profile.html',
        user=user
    )



@app.route('/admin/change-password', methods=['POST'])
def admin_change_password():
    user = getUserByToken()

    if not user or user['ROLE'] != 'admin':
        return redirect(url_for('login'))

    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')

    # Verify current password
    if not check_password_hash(user['PASSWORD'], current_password):
        return redirect(url_for('admin_profile'))

    hashed_password = generate_password_hash(new_password)

    
    # update admin profile in database
    updateAdminProfile(new_password=hashed_password, userid=user['PASSWORD'])

    return redirect(url_for('admin_profile'))



@app.route('/admin/logout')
def adminlogout():
    response = make_response(redirect(url_for('login')))

    # delete token cookie
    response.set_cookie(
        'token',
        '',
        expires=0,
        httponly=True
    )

    return response

#--------------common logout route for both admin and user-------------#

@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('user')))

    # delete JWT token cookie
    response.set_cookie(
        'token',
        '',
        expires=0,
        httponly=True
    )

    return response


# --------------------------------User Routes --------------------------------#
from database.user_utility import (
    show_category,
    searchProductsForUser,
    getUserProfile,
    getProductById,
    getUserCartItems,
    removeFromCart,
    updateCartQuantity,
    insertCartItem,
    increaseCartQuantity,
    getCartItem,
    placeOrder,
    myOrders,
    getPopularProducts

)
# helper fucntion 
def getDataFromToken():
    token = request.cookies.get('token')

    if not token:
        return redirect(url_for('login'))

    try:
        data = jwt.decode(
            token,
            app.config['SECRET_KEY'],
            algorithms=["HS256"]
        )
        return data
    except jwt.ExpiredSignatureError:
        return redirect(url_for('login'))
    except jwt.InvalidTokenError:
        return redirect(url_for('login'))

#User dashboard route
@app.route('/user')
@token_required(role='user')
def user():
    user = getUserByToken()
    name = user.get('NAME','Dear User')
    popular_products = getPopularProducts()
    return render_template(
        'user/user_dashboard.html',
        popular_products=popular_products,
        user_logged_in=True,
        username=name
    )
# user products route  
@app.route('/user/products', methods=['GET', 'POST'])
@token_required(role='user')
def user_products():

    user = getUserByToken()
    name = user.get('NAME', 'User')

    query = ""
    products = []

    token = request.cookies.get('token')
    if not token:
        return redirect(url_for('login'))
    if request.method == 'POST':
        query = request.form.get('query')
        products = searchProductsForUser(query)
    else:
        products = searchProductsForUser("") 

    return render_template(
        'user/user_products.html',
        products=products,
        query=query,
        username=name,
        user_logged_in=True

    )

#home route
@app.route('/user/home', methods=['GET', 'POST'])
@token_required(role='user')
def user_home():
    if request.method == 'POST':
        return redirect(url_for('user'))
    return render_template('user/user_dashboard.html')


# categories route
#user category___________
@app.route('/user/categories')
@token_required(role='user')
def user_categories():

    categories = [
        {"name": "Fashion", "slug": "fashion", "desc": "Men & women clothing", "image": "uploads/categories_images/fashion.png"},
        {"name": "Electronics", "slug": "electronics", "desc": "Mobiles, laptops & gadgets", "image": "uploads/categories_images/electronics.png"},
        {"name": "Shoes & Sneakers", "slug": "shoes", "desc": "Men & women footwear", "image": "uploads/categories_images/shoes.png"},
        {"name": "Audio", "slug": "audio", "desc": "Headphones, speakers & more", "image": "uploads/categories_images/audio.png"},
        {"name": "Beauty", "slug": "beauty", "desc": "Cosmetics & personal care", "image": "uploads/categories_images/beauty.png"},
        {"name": "Home & Kitchen", "slug": "home", "desc": "Appliances & essentials", "image": "uploads/categories_images/home.png"},
        {"name": "Toys & Games", "slug": "toys", "desc": "Children's toys and games", "image": "uploads/categories_images/toys.png"},
        {"name": "Books", "slug": "books", "desc": "Novels, textbooks & more", "image": "uploads/categories_images/books.png"},
        {"name": "Computers", "slug": "computers", "desc": "Laptops, desktops & accessories", "image": "uploads/categories_images/computers.png"},
        {"name": "Accessories", "slug": "accessories", "desc": 	"Phone cases, chargers & more", "image":"uploads/categories_images/accessories.png"},
    ]

    user = getUserByToken()
    name = user.get('NAME', 'User')

    category = request.args.get("category")
    print("CATEGORY RECEIVED:", category)  

    items = []

    if category:
        items = show_category(category)

    print("ITEM COUNT:", len(items)) 

    return render_template(
        "user/categories.html",
        categories=categories,
        items=items,
        selected_category=category,
        username=name,
        user_logged_in=True
    )

# add to cart route
@app.route('/add-to-cart', methods=['POST'])
@token_required(role='user')
def add_to_cart():
    
    print(getDataFromToken())
    user_data = getDataFromToken()
    
    user_id = user_data['userid']   # adjust if your token stores differently
    product_id = request.form.get('product_id')

    # Get product details
    product = getProductById(product_id)

    if not product:
        flash("Product not found", "danger")
        return redirect(request.referrer)

    # Check if already in cart
    existing = getCartItem(user_id, product_id)

    if existing:
        increaseCartQuantity(user_id, product_id)
    else:
        insertCartItem(user_id, product_id, product['PRICE'])

    flash("Added to cart successfully", "success")
    return redirect(url_for('view_cart'))


# orders route
@app.route('/user/checkout', methods=['GET', 'POST'])
@token_required(role='user')
def checkout():

    user = getUserByToken()   # from your token decorator
    name = user.get('NAME','Dear User')

    # fetch items and calculate total
    cart_items = getUserCartItems(user['USERID'])
    total_amount = sum(item.get('TOTAL_PRICE', 0) for item in cart_items)

    return render_template(
        "user/checkout.html",
        cart_items=cart_items,
        total_amount=total_amount,
        razorpay_key_id=RAZORPAY_KEY_ID,
        username=name,
        user_logged_in=True
    )

# buy now route
@app.route('/buy-now', methods=['POST'])
@token_required(role='user')
def buy_now():
    user = getUserByToken()
    name = user.get('NAME', 'User')
    user = getUserByToken()
    user_id = user['USERID']

    product_id = request.form.get('product_id')

    # Get product
    product = getProductById(product_id)
    if not product:
        flash("Product not found", "danger")
        return redirect(request.referrer)

    # Check if already in cart
    existing = getCartItem(user_id, product_id)

    if existing:
        increaseCartQuantity(user_id, product_id)
    else:
        insertCartItem(user_id, product_id, product['PRICE'])

    return redirect(url_for('checkout', username=name, user_logged_in=True))

# create razorpay order route
@app.route("/create-razorpay-order", methods=["POST"])
@token_required(role='user')
def create_razorpay_order():
    user = getUserByToken()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    amount = request.json.get("amount")  # rupees

    if not amount:
        return jsonify({"error": "Amount required"}), 400

    razorpay_order = razorpay_client.order.create({
        "amount": int(amount * 100),  # convert ₹ → paise
        "currency": "INR",
        "payment_capture": 1
    })

    return jsonify({
        "order_id": razorpay_order["id"],
        "amount": razorpay_order["amount"],
        "key": RAZORPAY_KEY_ID
    })

# verify payment route
@app.route("/verify-payment", methods=["POST"])
@token_required(role='user')
def verify_payment():
    data = request.get_json()

    try:
        # 1️⃣ Verify Razorpay signature (MOST IMPORTANT)
        razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": data["razorpay_order_id"],
            "razorpay_payment_id": data["razorpay_payment_id"],
            "razorpay_signature": data["razorpay_signature"]
        })

        # 2️⃣ Payment verified → place order
        user = getUserByToken()
        user_id = user["USERID"]

        address = data["address"]

        fullname = address["fullname"]
        phone = address["phone"]
        address_text = address["address"]
        city = address["city"]
        pincode = address["pincode"]

        # Get cart items
        cart_items = getUserCartItems(user_id)
        total_amount = sum(item["TOTAL_PRICE"] for item in cart_items)

        # 3️⃣ Call your existing placeOrder() function
        status, msg = placeOrder(
            userid=user_id,
            fullname=fullname,
            phone=phone,
            address=address_text,
            city=city,
            pincode=pincode,
            total_amount=total_amount,
            cart_items=cart_items,
            payment_method="CARD",
            payment_status="SUCCESS"
        )

        if not status:
            return jsonify({
                "status": "failed",
                "message": msg
            }), 400

        # ✅ SUCCESS
        return jsonify({
            "status": "success",
            "payment_id": data["razorpay_payment_id"]
        })

    except Exception as e:
        print("RAZORPAY VERIFY ERROR:", e)
        return jsonify({
            "status": "failed",
            "message": "Payment verification failed"
        }), 400
    
# place order route for COD
@app.route("/place-cod-order", methods=["POST"])
@token_required(role='user')
def place_cod_order():

    data = request.get_json()

    user = getUserByToken()
    user_id = user["USERID"]

    cart_items = getUserCartItems(user_id)
    total_amount = sum(item["TOTAL_PRICE"] for item in cart_items)

    status, msg = placeOrder(
        userid=user_id,
        fullname=data["fullname"],
        phone=data["phone"],
        address=data["address"],
        city=data["city"],
        pincode=data["pincode"],
        total_amount=total_amount,
        cart_items=cart_items,
        payment_method="COD",
        payment_status="PENDING"
    )

    if not status:
        return jsonify({"status": "failed"})

    return jsonify({"status": "success"})

# my orders route
@app.route('/user/orders')
@token_required(role='user')
def my_orders():
    # token_required has already validated the JWT and populated request.userid
    user = getUserByToken()
    name = user.get('NAME', 'User')
    if not user:
        # worst-case fallback, though token_required should have prevented this
        return redirect(url_for('login'))

    name = user.get('name', user.get('NAME', 'Dear User'))
    orders = myOrders(userid=user['USERID'])

    return render_template("user/user_orders.html", orders=orders,username=name, user_logged_in=True)

# cart route
@app.route('/user/cart')
@token_required(role='user')
def view_cart():
    user_data = getDataFromToken()
    user = getUserByToken()
    name = user.get('NAME', 'User')
    
    user_id = user_data['userid']  # adjust if needed

    cart_items = getUserCartItems(user_id)

    # Calculate grand total
    grand_total = sum(item['TOTAL_PRICE'] for item in cart_items)

    return render_template(
        'user/cart.html',
        cart_items=cart_items,
        grand_total=grand_total,
        username=name,
        user_logged_in=True
    )


# update quantity
@app.route('/update-cart-quantity', methods=['POST'])
@token_required(role='user')
def update_cart_quantity():
    user_data = getDataFromToken()
    user_id = user_data['userid']
    product_id = request.form.get('product_id')
    quantity = request.form.get('quantity')

    # update quantity
    updateCartQuantity(quantity=quantity, user_id=user_id, product_id=product_id)

    

    flash("Cart updated", "success")
    return redirect(url_for('view_cart'))

# remove from cart route
@app.route('/remove-from-cart', methods=['POST'])
@token_required(role='user')
def remove_from_cart():
    user_data = getDataFromToken()
    user_id = user_data['userid']
    product_id = request.form.get('product_id')

    # delete produt from cart
    removeFromCart(user_id=user_id, product_id=product_id)

    flash("Item removed from cart", "success")
    return redirect(url_for('view_cart'))

# user profile route
@app.route('/user/profile')
@token_required(role='user')
def user_profile():

    user = getUserByToken()
    name = user.get('NAME', 'User')
    user = getUserByToken()

    if not user:
        return redirect(url_for('login'))

    first_name = ""
    last_name = ""
    if user.get('NAME'):
        parts = user['NAME'].split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

    profile_image = (
        user['PROFILE_IMAGE']
        if user.get('PROFILE_IMAGE')
        else 'images/default_user.png'
    )

    return render_template(
        'user/user_profile.html',
        user=user,
        panel_name="User Panel",
        first_name=first_name,
        last_name=last_name,
        profile_image=profile_image,
        username=name,
        user_logged_in=True
    )


# main
if __name__ == "__main__":
    createTables()
    app.run(debug=True, port=5006)
     