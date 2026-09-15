from decimal import Decimal, InvalidOperation

from flask import abort, render_template, url_for, flash, redirect, request, jsonify, make_response
import json
from flask_wtf import form
from flask_login import login_user, logout_user, current_user, login_required

from user_application.invokes import invoke_http

from user_application.models import Users
from user_application.forms import RegistrationForm, LoginForm
from user_application import app, db, bcrypt, csrf
from user_application.utils import get_cart_cookie, get_checkout_cookie


CATALOGUE_URL = app.config['CATALOGUE_SERVICE_URL']
VENUE_URL = app.config['VENUE_SERVICE_URL']
CART_URL = app.config['CART_SERVICE_URL']
REVIEW_URL = app.config['REVIEW_SERVICE_URL']
PROCESS_REVIEW_URL = app.config['PROCESS_REVIEW_SERVICE_URL']
VIEW_ORDER_URL = app.config['VIEW_ORDER_SERVICE_URL']


def as_money(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0.00")


# =========================== DEFAULT ===========================
@app.route('/', methods=['GET'])
def home():
    catalogue_data = invoke_http(CATALOGUE_URL + "/api/v1/catalogue", method='GET')
    venue_data = invoke_http(VENUE_URL + "/api/v1/venues", method='GET')

    return render_template('catalogue.html', title="Catalogue", catalogue_data=catalogue_data, venue_data=venue_data)

# =========================== CATALOGUE / VENUE DISPLAY ===========================
@app.route('/catalogue/<catalogue_id>', methods=['GET', 'POST'])
@login_required
def catalogue_detail(catalogue_id):
    catalogue_data = invoke_http(CATALOGUE_URL + "/api/v1/catalogue/" + catalogue_id, method='GET')
    catalogue_review = invoke_http(REVIEW_URL + "/api/v1/reviews", method='GET', params={"product_id": catalogue_id})

    # Check if the 'data' and 'review' keys exist in the catalogue_review dictionary
    if 'data' in catalogue_review and 'reviews' in catalogue_review['data']:
        catalogue_review = catalogue_review['data']['reviews']
    else:
        # If either key doesn't exist, return an error message
        catalogue_review = []

    return render_template("catalogue-detail.html", title="Catalogue Detail", catalogue_data=catalogue_data['data'], catalogue_review=catalogue_review)


@app.route('/venue/<venue_id>', methods=['GET'])
@login_required
def venue_detail(venue_id):
    venue_data = invoke_http(VENUE_URL + "/api/v1/venues/" + venue_id, method='GET')
    venue_review = invoke_http(REVIEW_URL + "/api/v1/reviews", method='GET', params={"product_id": venue_id})

    # Check if the 'data' and 'review' keys exist in the catalogue_review dictionary
    if 'data' in venue_review and 'reviews' in venue_review['data']:
        venue_review = venue_review['data']['reviews']
    else:
        # If either key doesn't exist, return an error message
        venue_review = []


    return render_template("venue-detail.html", title="Venue Detail", venue_data=venue_data['data'], venue_review=venue_review)


# =========================== CART ===========================
@app.route('/cart', methods=['GET'])
@login_required
def cart():
    catalogue_arr = [] # [(a,b,c)]
    venue_arr = []
    total_amount = Decimal("0.00")
    combined_dict = {}

    if current_user.is_authenticated:   
        cart_data = invoke_http(CART_URL + "/api/v1/carts/" + current_user.user_id_email)

        if not isinstance(cart_data, dict) or 'data' not in cart_data:
            cart_data = {"data": {"cart_items": [], "cart_venues": []}}

        for product_type in cart_data['data']:
            if product_type == "cart_items":
                for data in cart_data['data'][product_type]:
                    item_id = data['item_id']
                    quantity = data['quantity']
                    specific_item = invoke_http(CATALOGUE_URL + '/api/v1/catalogue/' + item_id, method='GET')
                    item_name = specific_item['data']['item_name']
                    item_image = specific_item['data']['item_img']
                    item_price = as_money(specific_item['data']['item_price'])
                    total_amount += quantity * item_price
                    catalogue_arr.append((item_image, item_name, quantity, item_price, item_id))

            elif product_type == "cart_venues":
                for data in cart_data['data'][product_type]:
                    venue_id = data['venue_id']
                    specific_venue = invoke_http(VENUE_URL + '/api/v1/venues/' + venue_id, method='GET')
                    venue_image = specific_venue['data']['venue_img']
                    venue_name = specific_venue['data']['venue_name']
                    venue_price = as_money(specific_venue['data']['venue_price'])
                    total_amount += venue_price
                    venue_arr.append((venue_image, venue_name, venue_price, venue_id, data['datetime']))

        combined_dict = {
            "catalogue_cart_details": [
                [item[0], item[1], item[2], str(item[3]), item[4]] for item in catalogue_arr
            ],
            "venue_cart_details": [
                [item[0], item[1], str(item[2]), item[3], item[4]] for item in venue_arr
            ],
            "total_amount": str(total_amount),
        }

    # returns template
    resp = make_response(render_template("cart.html", title="Cart", catalogue_arr=catalogue_arr, venue_arr=venue_arr, total_amount=total_amount))
    
    # setting cookie
    resp.set_cookie('cart_details', json.dumps(combined_dict))

    
    return resp

@app.route('/add-to-cart/<prod_id>', methods=['GET','POST'])
@login_required
def add_to_cart(prod_id):
    if request.method == 'POST':
        if current_user.is_authenticated:
            user_id = current_user.user_id_email
            result_json_to_return = {}
            
            if prod_id[0] == "i":
                try:
                    quantity = int(request.form['quantity'])
                except (TypeError, ValueError):
                    flash('Item quantity must be a positive whole number.', 'danger')
                    return redirect(url_for('catalogue_detail', catalogue_id=prod_id))
                result_json_to_return["quantity"] = quantity

            if prod_id[0] == "v":    
                venue_datetime = request.form['venue_datetime']
                result_json_to_return["venue_datetime"] = venue_datetime

            invoke_http(CART_URL + "/api/v1/carts/" + user_id + "/products/" + prod_id, method='POST', json=result_json_to_return)

            # for redirection
    if prod_id[0] == "i":
        flash('Item has been added to cart!', 'success')
        return redirect(url_for('catalogue_detail', catalogue_id=prod_id))
    else:
        flash('Venue has been added to cart!', 'success')
        return redirect(url_for('venue_detail', venue_id=prod_id))
    

@app.route('/remove_from_cart/<prod_id>', methods=['POST'])
@login_required
def remove_from_cart(prod_id):
    if request.method == 'POST':
        if current_user.is_authenticated:
            user_id = current_user.user_id_email
            invoke_http(CART_URL + "/api/v1/carts/" + user_id + "/products/" + prod_id, method='DELETE')

            flash(f'Item {prod_id} has been removed from cart!', 'info')
    return redirect(url_for('cart'))

@app.route('/increase-cart-quantity/<prod_id>', methods=['POST'])
@login_required
def increase_cart_quantity(prod_id):
    if request.method == "POST":
        if current_user.is_authenticated:
            user_id = current_user.user_id_email
            cart_data = invoke_http(CART_URL + "/api/v1/carts/" + user_id, method='GET')
            cart_item = next(
                (item for item in cart_data.get("data", {}).get("cart_items", []) if item["item_id"] == prod_id),
                None,
            )
            if cart_item:
                invoke_http(
                    CART_URL + "/api/v1/carts/" + user_id + "/items/" + prod_id,
                    method='PATCH',
                    json={"quantity": cart_item["quantity"] + 1},
                )

            flash(f'Item {prod_id} quantity has been increased!', 'info')

    return redirect(url_for('cart'))


@app.route('/decrease-cart-quantity/<prod_id>', methods=['POST'])
@login_required
def decrease_cart_quantity(prod_id):
    if request.method == "POST":
        if current_user.is_authenticated:
            user_id = current_user.user_id_email
            cart_data = invoke_http(CART_URL + "/api/v1/carts/" + user_id, method='GET')
            cart_item = next(
                (item for item in cart_data.get("data", {}).get("cart_items", []) if item["item_id"] == prod_id),
                None,
            )
            if cart_item and cart_item["quantity"] > 1:
                invoke_http(
                    CART_URL + "/api/v1/carts/" + user_id + "/items/" + prod_id,
                    method='PATCH',
                    json={"quantity": cart_item["quantity"] - 1},
                )

            flash(f'Item {prod_id} quantity has been decreased!', 'info')

    return redirect(url_for('cart'))

# =========================== ORDERS ===========================
@app.route('/order-logs', methods=['GET', "POST"])
@login_required
def order_logs():
    order_details = []
    if request.method == "GET":
        user_id = current_user.user_id_email
        # call view_order complex microservice

        order_data = invoke_http(VIEW_ORDER_URL + "/api/v1/orders", method="GET", params={"user_id": user_id})
            

        if order_data['code'] == 200:
            order_details = order_data["orders"]
        else:
            flash("No orders found!", "info")
            return redirect(url_for('cart'))

    return render_template("order-logs.html", title="Order Logs", order_details=order_details, refund_service_url=app.config['REFUND_SERVICE_URL'])


# order details view
@app.route('/order-logs/<order_id>', methods=['GET', "POST"])
@login_required
def order_details(order_id):
    user_id = current_user.user_id_email

    order_data = invoke_http(VIEW_ORDER_URL + "/api/v1/orders/" + order_id, method="GET")
    user_review_data = invoke_http(REVIEW_URL + "/api/v1/reviews", method="GET", params={"user_id": user_id})

    if (order_data.get("code") != 200
            or order_id not in order_data
            or order_data[order_id].get("user_id") != user_id):
        flash("Order could not be found.", "danger")
        return redirect(url_for('order_logs'))

    order_data[order_id]["total_amount"] = as_money(order_data[order_id]["total_amount"])
    for item in order_data[order_id]["order_items"]:
        item["item_price"] = as_money(item["item_price"])
    if "venue" in order_data[order_id]:
        order_data[order_id]["venue"]["venue_price"] = as_money(order_data[order_id]["venue"]["venue_price"])
    

        # order_items: arr
    for item in order_data[order_id]["order_items"]:
        item["isReviewed"] = ""
        item_id = item["item_id"]
        if user_review_data["code"] in range(200, 300):
            for review in user_review_data["data"]["reviews"]:
                if item_id == review["prod_id"]:
                    isReviewed_dict = {}
                    rating = review["rating"]
                    rating_desc = review["rating_desc"]
                    isReviewed_dict["rating"] = rating
                    isReviewed_dict["rating_desc"] = rating_desc
                    item["isReviewed"] = isReviewed_dict
                    break
    
    # venue: venue_id
    if "venue" in order_data[order_id]:
        order_venue_id = order_data[order_id]["venue"]["venue_id"]
        venue_data = order_data[order_id]["venue"]
        venue_data["isReviewed"] = ""
        if user_review_data["code"] in range(200, 300):
            for review in user_review_data["data"]["reviews"]:
                if order_venue_id == review["prod_id"]:
                    isReviewed_dict = {}
                    rating = review["rating"]
                    rating_desc = review["rating_desc"]
                    isReviewed_dict["rating"] = rating
                    isReviewed_dict["rating_desc"] = rating_desc
                    venue_data["isReviewed"] = isReviewed_dict
                    break    
        
    return render_template("order-details.html", title="Order Details",user_id=user_id, order_data=order_data, order_id=order_id)


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    delivery_address, delivery_date = "", ""
    catalogue_arr, venue_arr, total_amount = [], [], 0

    # get cart details from cookie
    cart_data = get_cart_cookie('cart_details')

    if cart_data:
        catalogue_arr, venue_arr, total_amount = cart_data["catalogue_cart_details"], cart_data["venue_cart_details"], cart_data["total_amount"]
        
        total_amount = cart_data["total_amount"]

    # form submission
    if request.method == "POST":
        # get payment details: delivery_address and delivery_date
        delivery_address = request.form["delivery_address"]
        delivery_date = request.form["delivery_date"]

        # create checkout_details cookie
        resp = make_response(redirect(url_for('stripe_payment')))

        resp.set_cookie('checkout_details', json.dumps({"delivery_address": delivery_address, "delivery_date": delivery_date}))

        return resp

    
    return render_template("checkout.html", title="Checkout", catalogue_arr=catalogue_arr, venue_arr=venue_arr, total_amount=total_amount)


@app.route('/stripe-payment', methods=['GET', 'POST'])
@login_required
def stripe_payment():
    cart_cookie = get_cart_cookie('cart_details')
    checkout_cookie = get_checkout_cookie('checkout_details')

    return render_template("stripe_payment.html", title="Stripe Payment", cart_cookie=cart_cookie, checkout_cookie=checkout_cookie, email=current_user.user_id_email, username=current_user.name, process_order_url=app.config['PROCESS_ORDER_SERVICE_URL'])




# =========================== REVIEW ===========================
@app.route('/add-review/<prod_id>', methods=['GET', 'POST'])
@login_required
def add_review(prod_id):
    if request.method == 'POST':
        if current_user.is_authenticated:
            user_id = current_user.user_id_email
            rating = int(request.form['rating'])
            review = request.form['review']

            review_data = {"rating": rating, "rating_desc": review}

            # call add_review microservice
            review_data["user_id"] = user_id
            review_data["prod_id"] = prod_id
            response = invoke_http(PROCESS_REVIEW_URL + '/api/v1/reviews', method='POST', json=review_data)
            if prod_id[0] == "i":
                if response['code'] in range(200, 300):
                    flash(f'Your review has been added!', 'success')
                    return redirect(url_for('catalogue_detail', catalogue_id=prod_id))
                else:
                    return redirect(url_for('catalogue_detail', catalogue_id=prod_id))
            else:
                if response['code'] in range(200, 300):
                    flash(f'Your review has been added!', 'success')
                    return redirect(url_for('venue_detail', venue_id=prod_id))
                else:
                    return redirect(url_for('venue_detail', venue_id=prod_id))

@app.route('/review/edit_review/<user_id>/<prod_id>', methods=['POST'])
@login_required
def update_review(user_id, prod_id):
    if user_id != current_user.user_id_email:
        abort(403)

    result_json_to_return = {}
    rating = int(request.form["rating"])
    rating_desc = request.form["review"]


    result_json_to_return["prod_id"] = prod_id
    result_json_to_return["user_id"] = user_id
    result_json_to_return["rating"] = rating
    result_json_to_return["rating_desc"] = rating_desc

    response = invoke_http(PROCESS_REVIEW_URL + "/api/v1/reviews/" + user_id + "/" + prod_id, method="PATCH", json=result_json_to_return)

    if prod_id[0] == "i":
        return redirect(url_for('catalogue_detail', catalogue_id=prod_id))
        
    else:
        return redirect(url_for('venue_detail', venue_id=prod_id))

    

# =========================== AUTH ===========================
@app.route('/register', methods=['GET', 'POST'])
@csrf.exempt  # prevent form spams
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            'utf-8')  # To make a string instead of byte

        user = Users(user_id_email=form.email.data.lower(), name=form.username.data.lower(), password=hashed_password)
        db.session.add(user)
        db.session.commit()

        flash('Your account has been created! You are now able to login', 'success')

        return redirect(url_for('login'))

    return render_template('register.html', title="Register", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(name=form.username.data).first()

        if user and user.role == "admin" and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('home'))

        if user and user.role == "user" and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            # # set cookie
            # response = make_response("Cookie set for user")
            # response.set_cookie('user_id_email', user.user_id_email)

            # return response 
            return redirect(url_for('home'))
        else:
            flash("Login unsuccessful. Please check email and password.", "danger")

    return render_template('login.html', title="Login", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))
