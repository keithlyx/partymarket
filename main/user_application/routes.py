from flask import render_template, url_for, flash, redirect, request, jsonify, make_response
import json
from flask_wtf import form
from flask_login import login_user, logout_user, current_user, login_required

from user_application.invokes import invoke_http

from user_application.models import Users
from user_application.forms import RegistrationForm, LoginForm
from user_application import app, db, bcrypt, csrf
from user_application.utils import get_cart_cookie, get_checkout_cookie


# =========================== DEFAULT ===========================
@app.route('/', methods=['GET'])
def home():
    catalogue_data = invoke_http("http://localhost:5004/api/v1/catalogue", method='GET')
    venue_data = invoke_http("http://localhost:5003/api/v1/venue", method='GET')

    return render_template('catalogue.html', title="Catalogue", catalogue_data=catalogue_data, venue_data=venue_data)

# =========================== CATALOGUE / VENUE DISPLAY ===========================
@app.route('/catalogue/<catalogue_id>', methods=['GET', 'POST'])
@login_required
def catalogue_detail(catalogue_id):
    catalogue_data = invoke_http("http://localhost:5004/api/v1/catalogue/" + catalogue_id, method='GET')
    catalogue_review = invoke_http("http://localhost:5007/api/v1/review/product/" + catalogue_id, method='GET')

    # Check if the 'data' and 'review' keys exist in the catalogue_review dictionary
    if 'data' in catalogue_review and 'review' in catalogue_review['data']:
        catalogue_review = catalogue_review['data']['review']
    else:
        # If either key doesn't exist, return an error message
        catalogue_review = []
        print("No reviews made for this item yet.")

    return render_template("catalogue-detail.html", title="Catalogue Detail", catalogue_data=catalogue_data['data'], catalogue_review=catalogue_review)


@app.route('/venue/<venue_id>', methods=['GET'])
@login_required
def venue_detail(venue_id):
    venue_data = invoke_http("http://localhost:5003/api/v1/venue/" + venue_id, method='GET')
    venue_review = invoke_http("http://localhost:5007/api/v1/review/product/" + venue_id, method='GET')

    # Check if the 'data' and 'review' keys exist in the catalogue_review dictionary
    if 'data' in venue_review and 'review' in venue_review['data']:
        venue_review = venue_review['data']['review']
    else:
        # If either key doesn't exist, return an error message
        venue_review = []
        print("No reviews made for this venue yet.")


    return render_template("venue-detail.html", title="Venue Detail", venue_data=venue_data['data'], venue_review=venue_review)


# =========================== CART ===========================
@app.route('/cart', methods=['GET'])
@login_required
def cart():
    catalogue_arr = [] # [(a,b,c)]
    venue_arr = []
    total_amount = 0
    combined_dict = {}

    if current_user.is_authenticated:   
        cart_data = invoke_http("http://localhost:5005/api/v1/get_cart/" + current_user.user_id_email)

        if 'data' not in cart_data and 'cart_items' not in cart_data and 'cart_venue' not in cart_data:
            cart_data = {}

        # if not cart_data:
        #     cart_data = {'data': {'cart_items': [], 'cart_venue': []}}
        else:
            for product_type in cart_data['data']:
                if product_type == "cart_items":
                    for data in cart_data['data'][product_type]:
                        item_id = data['item_id']
                        quantity = data['quantity']
                        specific_item = invoke_http('http://localhost:5004/api/v1/catalogue/' + item_id, method='GET')
                        
                        # Microservice product details
                        item_name = specific_item['data']['item_name']
                        item_image = specific_item['data']['item_img']
                        item_price = specific_item['data']['item_price']

                        total_amount += quantity * item_price

                        catalogue_arr.append((item_image, item_name,quantity, item_price, item_id))

                else:
                    for data in cart_data['data'][product_type]:

                        venue_id = data['venue_id']
                        specific_venue = invoke_http('http://localhost:5003/api/v1/venue/' + venue_id, method='GET')

                        # Microservice product details
  
                        venue_image = specific_venue['data']['venue_img']
                        venue_name = specific_venue['data']['venue_name']
                        venue_price = specific_venue['data']['venue_price']

                        total_amount += venue_price

                        venue_arr.append((venue_image, venue_name,venue_price, venue_id))

                

            # Converting to json string
            combined_dict = {"catalogue_cart_details": catalogue_arr, "venue_cart_details": venue_arr, "total_amount":total_amount}

    # returns template
    resp = make_response(render_template("cart.html", title="Cart", catalogue_arr=catalogue_arr, venue_arr=venue_arr, total_amount=total_amount))
    
    # setting cookie
    resp.set_cookie('cart_details', json.dumps(combined_dict))

    # print(get_cart_cookie('cart_details'))
    
    return resp

@app.route('/add-to-cart/<prod_id>', methods=['GET','POST'])
def add_to_cart(prod_id):
    if request.method == 'POST':
        if current_user.is_authenticated:
            user_id = current_user.user_id_email
            result_json_to_return = {}
            
            if prod_id[0] == "i":
                quantity = request.form['quantity']
                result_json_to_return["quantity"] = quantity

            if prod_id[0] == "v":    
                venue_datetime = request.form['venue_datetime']
                result_json_to_return["venue_datetime"] = venue_datetime

            print(result_json_to_return)
            invoke_http("http://localhost:5005/api/v1/add_cart/" + user_id + "/" + prod_id, method='POST', json=result_json_to_return)

            # for redirection
    if prod_id[0] == "i":
        flash('Item has been added to cart!', 'success')
        return redirect(url_for('catalogue_detail', catalogue_id=prod_id))
    else:
        flash('Venue has been added to cart!', 'success')
        return redirect(url_for('venue_detail', venue_id=prod_id))
    

@app.route('/remove_from_cart/<prod_id>', methods=['POST'])
def remove_from_cart(prod_id):
    if request.method == 'POST':
        if current_user.is_authenticated:
            user_id = current_user.user_id_email
            invoke_http("http://localhost:5005/api/v1/remove-from-cart/" + prod_id + "/" + user_id, method='POST')

            flash(f'Item {prod_id} has been removed from cart!', 'info')
    return redirect(url_for('cart'))

@app.route('/increase-cart-quantity/<prod_id>', methods=['POST'])
def increase_cart_quantity(prod_id):
    if request.method == "POST":
        if current_user.is_authenticated:
            user_id = current_user.user_id_email
            invoke_http("http://localhost:5005/api/v1/increase-cart-quantity/" + prod_id + "/" + user_id, method='POST')

            flash(f'Item {prod_id} quantity has been increased!', 'info')

    return redirect(url_for('cart'))


@app.route('/decrease-cart-quantity/<prod_id>', methods=['POST'])
def decrease_cart_quantity(prod_id):
    if request.method == "POST":
        if current_user.is_authenticated:
            user_id = current_user.user_id_email
            invoke_http("http://localhost:5005/api/v1/decrease-cart-quantity/" + prod_id + "/" + user_id, method='POST')

            flash(f'Item {prod_id} quantity has been decreased!', 'info')

    return redirect(url_for('cart'))

# =========================== ORDERS ===========================
@app.route('/order-logs', methods=['GET', "POST"])
def order_logs():
    print("=========================== orderlogs view ===========================")
    order_details = []
    if request.method == "GET":
        if current_user.is_authenticated:
            user_id = current_user.user_id_email
            # call view_order complex microservice

            order_data = invoke_http("http://localhost:5300/api/v1/get_order_by_user/" + user_id, method="GET")
            

            if order_data['code'] == 200:                
                order_details = order_data["orders"]
                
                print(order_details)
            else:
                flash("No orders found!", "info")
                return redirect(url_for('cart'))

    return render_template("order-logs.html", title="Order Logs", order_details=order_details)


# order details view
@app.route('/order-logs/<order_id>', methods=['GET', "POST"])
def order_details(order_id):
    print("=========================== order details view ===========================")
    user_id = current_user.user_id_email

    order_data = invoke_http("http://localhost:5300/api/v1/get_order_by_order/" + order_id, method="GET")
    print(order_data)
    print("============================================")
    user_review_data = invoke_http("http://localhost:5007/api/v1/review/user/" + user_id, method="GET")
    

        # order_items: arr
    for item in order_data[order_id]["order_items"]:
        item["isReviewed"] = ""
        item_id = item["item_id"]
        if user_review_data["code"] in range(200, 401):
            for review in user_review_data["data"]["review"]:
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
        if user_review_data["code"] in range(200, 401):
            for review in user_review_data["data"]["review"]:
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

        # invoke_http("http://localhost:5200/api/v1/get_cart/" + user_id + "/" + str(total_amount), method="POST")
    
    return render_template("checkout.html", title="Checkout", catalogue_arr=catalogue_arr, venue_arr=venue_arr, total_amount=total_amount)


@app.route('/stripe-payment', methods=['GET', 'POST'])
def stripe_payment():
    cart_cookie = get_cart_cookie('cart_details')
    checkout_cookie = get_cart_cookie('checkout_details')

    return render_template("stripe_payment.html", title="Stripe Payment", cart_cookie=cart_cookie, checkout_cookie=checkout_cookie, email=current_user.user_id_email,username=current_user.name)




# =========================== REVIEW ===========================
@app.route('/add-review/<prod_id>', methods=['GET', 'POST'])
def add_review(prod_id):
    if request.method == 'POST':
        if current_user.is_authenticated:
            user_id = current_user.user_id_email
            rating = int(request.form['rating'])
            review = request.form['review']

            print("------------------------------------------------------")
            print(rating, review)
            print(type(rating))
            review_data = {"rating": rating, "rating_desc": review}
            print(type(review_data))

            # call add_review microservice
            response = invoke_http(f'http://localhost:5400/api/v1/review/add_review/{user_id}/{prod_id}', method='POST', json=review_data)
            print(response)
            if prod_id[0] == "i":
                if response['code'] in range(200, 401):
                    print(response)
                    flash(f'Your review has been added!', 'success')
                    return redirect(url_for('catalogue_detail', catalogue_id=prod_id))
                else:
                    print(response)
                    # flash(f'Your review has not been added!', 'warning')
                    return redirect(url_for('catalogue_detail', catalogue_id=prod_id))
            else:
                if response['code'] in range(200, 401):
                    print(response)
                    flash(f'Your review has been added!', 'success')
                    return redirect(url_for('venue_detail', venue_id=prod_id))
                else:
                    print(response)
                    # flash(f'Your review has not been added!', 'warning')
                    return redirect(url_for('venue_detail', venue_id=prod_id))

@app.route('/review/edit_review/<user_id>/<prod_id>', methods=['POST'])
def update_review(user_id, prod_id):
    result_json_to_return = {}
    print("HELLOOOOOOOOOOOOOOOOOOOOO")
    rating = int(request.form["rating"])
    rating_desc = request.form["review"]

    print(rating, rating_desc)

    result_json_to_return["prod_id"] = prod_id
    result_json_to_return["user_id"] = user_id
    result_json_to_return["rating"] = rating
    result_json_to_return["rating_desc"] = rating_desc

    response = invoke_http("http://localhost:5400/api/v1/review/edit_review/" + user_id + "/" + prod_id, method="PUT", json=result_json_to_return)
    print(response)

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
