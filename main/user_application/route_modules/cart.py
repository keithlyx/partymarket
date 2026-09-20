import json
from decimal import Decimal

from flask import flash, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from user_application import app
from user_application.invokes import invoke_http
from .common import CART_URL, CATALOGUE_URL, VENUE_URL, as_money


@app.route('/cart', methods=['GET'])
@login_required
def cart():
    catalogue_items = []
    venue_items = []
    total_amount = Decimal("0.00")
    cart_data = invoke_http(
        CART_URL + "/api/v1/carts/" + current_user.user_id_email,
        method='GET',
    )

    if not isinstance(cart_data, dict) or 'data' not in cart_data:
        cart_data = {"data": {"cart_items": [], "cart_venues": []}}

    for data in cart_data['data'].get("cart_items", []):
        item_id = data['item_id']
        quantity = data['quantity']
        specific_item = invoke_http(
            CATALOGUE_URL + '/api/v1/catalogue/' + item_id,
            method='GET',
        )
        try:
            item_price = as_money(specific_item['data']['item_price'])
        except (KeyError, TypeError, ValueError):
            flash('Cart data could not be loaded.', 'danger')
            return redirect(url_for('home'))
        total_amount += quantity * item_price
        catalogue_items.append((
            specific_item['data']['item_img'],
            specific_item['data']['item_name'],
            quantity,
            item_price,
            item_id,
        ))

    for data in cart_data['data'].get("cart_venues", []):
        venue_id = data['venue_id']
        specific_venue = invoke_http(
            VENUE_URL + '/api/v1/venues/' + venue_id,
            method='GET',
        )
        try:
            venue_price = as_money(specific_venue['data']['venue_price'])
        except (KeyError, TypeError, ValueError):
            flash('Cart data could not be loaded.', 'danger')
            return redirect(url_for('home'))
        total_amount += venue_price
        venue_items.append((
            specific_venue['data']['venue_img'],
            specific_venue['data']['venue_name'],
            venue_price,
            venue_id,
            data['datetime'],
        ))

    cart_details = {
        "catalogue_cart_details": [
            [image, name, quantity, str(price), item_id]
            for image, name, quantity, price, item_id in catalogue_items
        ],
        "venue_cart_details": [
            [image, name, str(price), venue_id, venue_datetime]
            for image, name, price, venue_id, venue_datetime in venue_items
        ],
        "total_amount": str(total_amount),
    }
    response = make_response(render_template(
        "cart.html",
        title="Cart",
        catalogue_arr=catalogue_items,
        venue_arr=venue_items,
        total_amount=total_amount,
    ))
    response.set_cookie('cart_details', json.dumps(cart_details))
    return response


@app.route('/add-to-cart/<prod_id>', methods=['POST'])
@login_required
def add_to_cart(prod_id):
    user_id = current_user.user_id_email
    cart_payload = {}

    if prod_id.startswith("i"):
        try:
            cart_payload["quantity"] = int(request.form['quantity'])
        except (KeyError, TypeError, ValueError):
            flash('Item quantity must be a positive whole number.', 'danger')
            return redirect(url_for('catalogue_detail', catalogue_id=prod_id))
        redirect_target = url_for('catalogue_detail', catalogue_id=prod_id)
        success_message = 'Item has been added to cart!'
    elif prod_id.startswith("v"):
        cart_payload["venue_datetime"] = request.form['venue_datetime']
        redirect_target = url_for('venue_detail', venue_id=prod_id)
        success_message = 'Venue has been added to cart!'
    else:
        flash('Invalid product.', 'danger')
        return redirect(url_for('home'))

    invoke_http(
        CART_URL + "/api/v1/carts/" + user_id + "/products/" + prod_id,
        method='POST',
        json=cart_payload,
    )
    flash(success_message, 'success')
    return redirect(redirect_target)


@app.route('/remove_from_cart/<prod_id>', methods=['POST'])
@login_required
def remove_from_cart(prod_id):
    user_id = current_user.user_id_email
    invoke_http(
        CART_URL + "/api/v1/carts/" + user_id + "/products/" + prod_id,
        method='DELETE',
    )
    flash(f'Item {prod_id} has been removed from cart!', 'info')
    return redirect(url_for('cart'))


def _change_cart_quantity(prod_id, amount, message):
    user_id = current_user.user_id_email
    cart_data = invoke_http(CART_URL + "/api/v1/carts/" + user_id, method='GET')
    cart_items = cart_data.get("data", {}).get("cart_items", [])
    cart_item = next((item for item in cart_items if item["item_id"] == prod_id), None)
    if cart_item and cart_item["quantity"] + amount > 0:
        invoke_http(
            CART_URL + "/api/v1/carts/" + user_id + "/items/" + prod_id,
            method='PATCH',
            json={"quantity": cart_item["quantity"] + amount},
        )
    flash(message, 'info')
    return redirect(url_for('cart'))


@app.route('/increase-cart-quantity/<prod_id>', methods=['POST'])
@login_required
def increase_cart_quantity(prod_id):
    return _change_cart_quantity(
        prod_id,
        amount=1,
        message=f'Item {prod_id} quantity has been increased!',
    )


@app.route('/decrease-cart-quantity/<prod_id>', methods=['POST'])
@login_required
def decrease_cart_quantity(prod_id):
    return _change_cart_quantity(
        prod_id,
        amount=-1,
        message=f'Item {prod_id} quantity has been decreased!',
    )
