import json
from uuid import uuid4

from flask import flash, jsonify, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from user_application import app
from user_application.invokes import invoke_http
from user_application.utils import get_cart_cookie, get_checkout_cookie
from .common import PROCESS_ORDER_URL, REFUND_URL, REVIEW_URL, VIEW_ORDER_URL, as_money


def _reviews_by_product(response):
    if not isinstance(response, dict) or response.get('code') not in range(200, 300):
        return {}
    review_data = response.get('data')
    if not isinstance(review_data, dict):
        return {}
    reviews = review_data.get('reviews', [])
    if not isinstance(reviews, list):
        return {}
    return {
        review.get('prod_id'): {
            "rating": review.get('rating'),
            "rating_desc": review.get('rating_desc'),
        }
        for review in reviews
        if isinstance(review, dict) and review.get('prod_id')
    }


@app.route('/order-logs', methods=['GET'])
@login_required
def order_logs():
    user_id = current_user.user_id_email
    order_data = invoke_http(
        VIEW_ORDER_URL + "/api/v1/orders",
        method="GET",
        params={"user_id": user_id},
    )
    if order_data.get('code') != 200:
        flash("No orders found!", "info")
        return redirect(url_for('cart'))
    return render_template(
        "order-logs.html",
        title="Order Logs",
        order_details=order_data["data"]["orders"],
    )


@app.route('/api/v1/refunds', methods=['POST'])
@login_required
def create_refund():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("order_id"), str) or not data["order_id"].strip():
        return jsonify({"code": 400, "message": "order_id is required."}), 400

    result = invoke_http(
        REFUND_URL + "/api/v1/refunds",
        method="POST",
        json={"order_id": data["order_id"], "user_id": current_user.user_id_email},
    )
    return jsonify(result), result.get("code", 502)


@app.route('/order-logs/<order_id>', methods=['GET'])
@login_required
def order_details(order_id):
    user_id = current_user.user_id_email
    order_data = invoke_http(VIEW_ORDER_URL + "/api/v1/orders/" + order_id, method="GET")
    review_data = invoke_http(
        REVIEW_URL + "/api/v1/reviews",
        method="GET",
        params={"user_id": user_id},
    )

    if order_data.get("code") != 200:
        flash("Order could not be found.", "danger")
        return redirect(url_for('order_logs'))

    order = order_data.get("data", {}).get("order")
    if not order or order.get("user_id") != user_id:
        flash("Order could not be found.", "danger")
        return redirect(url_for('order_logs'))

    try:
        order["total_amount"] = as_money(order["total_amount"])
        for item in order["order_items"]:
            item["item_price"] = as_money(item["item_price"])
        if "venue" in order:
            order["venue"]["venue_price"] = as_money(order["venue"]["venue_price"])
    except (KeyError, TypeError, ValueError):
        flash("Order data could not be displayed.", "danger")
        return redirect(url_for('order_logs'))

    reviews_by_product = _reviews_by_product(review_data)
    for item in order["order_items"]:
        item["isReviewed"] = reviews_by_product.get(item["item_id"], "")
    if "venue" in order:
        venue = order["venue"]
        venue["isReviewed"] = reviews_by_product.get(venue["venue_id"], "")

    return render_template(
        "order-details.html",
        title="Order Details",
        user_id=user_id,
        order_data={order_id: order},
        order_id=order_id,
    )


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_data = get_cart_cookie('cart_details') or {}
    catalogue_arr = cart_data.get("catalogue_cart_details", [])
    venue_arr = cart_data.get("venue_cart_details", [])
    total_amount = cart_data.get("total_amount", 0)

    if request.method == "POST":
        checkout_details = {
            "delivery_address": request.form["delivery_address"],
            "delivery_date": request.form["delivery_date"],
        }
        response = make_response(redirect(url_for('stripe_payment')))
        response.set_cookie('checkout_details', json.dumps(checkout_details))
        return response

    return render_template(
        "checkout.html",
        title="Checkout",
        catalogue_arr=catalogue_arr,
        venue_arr=venue_arr,
        total_amount=total_amount,
    )


@app.route('/api/v1/checkout', methods=['POST'])
@login_required
def create_checkout_order():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"code": 400, "message": "Request payload must be a JSON object."}), 400

    fields = [data.get(name) for name in ("token", "checkout_id", "delivery_address", "delivery_datetime")]
    if not all(isinstance(value, str) and value.strip() for value in fields):
        return jsonify({
            "code": 400,
            "message": "Payment token, delivery address and delivery date are required.",
        }), 400

    result = invoke_http(
        PROCESS_ORDER_URL + "/api/v1/orders",
        method="POST",
        json={
            "user_id": current_user.user_id_email,
            "token": data["token"],
            "idempotency_key": data["checkout_id"],
            "delivery_address": data["delivery_address"],
            "delivery_datetime": data["delivery_datetime"],
        },
    )
    return jsonify(result), result.get("code", 502)


@app.route('/stripe-payment', methods=['GET', 'POST'])
@login_required
def stripe_payment():
    return render_template(
        "stripe_payment.html",
        title="Stripe Payment",
        checkout_cookie=get_checkout_cookie('checkout_details'),
        checkout_url=url_for('create_checkout_order'),
        checkout_id=uuid4().hex,
    )
