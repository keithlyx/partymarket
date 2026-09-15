from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from os import environ
from invokes import invoke_http
import amqp_setup
import pika
import json
import logging
from decimal import Decimal, InvalidOperation

app = Flask(__name__)
logger = logging.getLogger(__name__)

payment_url = environ.get('PAYMENT_URL') or "http://payment:5008/api/v1/refunds"
order_url = environ.get('ORDER_URL') or "http://order:5006/api/v1/orders"


@app.route('/api/v1/refunds', methods=["POST"])
def refund():
    data = request.get_json(silent=True)
    if (not isinstance(data, dict) or not isinstance(data.get("order_id"), str)
            or not data["order_id"].strip()
            or not isinstance(data.get("user_id"), str)
            or not data["user_id"].strip()):
        return jsonify({
            "code": 400,
            "message": "Request must include order_id and user_id.",
        }), 400

    order_response = invoke_http(order_url + "/" + data["order_id"], method="GET")
    if order_response.get("code") not in range(200, 300):
        return jsonify({
            "code": order_response.get("code", 502),
            "message": "Order could not be retrieved.",
        }), order_response.get("code", 502)

    order = order_response.get("order")
    if not isinstance(order, dict) or order.get("user_id") != data["user_id"]:
        return jsonify({
            "code": 403,
            "message": "You are not allowed to refund this order.",
        }), 403

    if order.get("order_status") == "Refunded":
        return jsonify({
            "code": 409,
            "message": "This order has already been refunded.",
        }), 409
    if order.get("order_status") != "Accepted":
        return jsonify({
            "code": 409,
            "message": "This order is not eligible for a refund.",
        }), 409

    try:
        amount = Decimal(str(order["total_amount"]))
    except (KeyError, InvalidOperation, ValueError):
        return jsonify({
            "code": 502,
            "message": "Order service returned an invalid order amount.",
        }), 502
    if not amount.is_finite() or amount <= 0 or amount.as_tuple().exponent < -2:
        return jsonify({
            "code": 502,
            "message": "Order service returned an invalid order amount.",
        }), 502

    data["amount_cents"] = int(amount * 100)
    return process_refund(data)


def process_refund(data):
    order_id = data["order_id"]
    refund = invoke_http(payment_url, method="POST", json={
        "charge_id": order_id,
        "amount_cents": data["amount_cents"],
    })
    if refund["code"] not in range(200, 300):
        return jsonify({
            "code": refund["code"],
            "message": "Payment provider rejected the refund request.",
        }), refund["code"]

    updated_order = invoke_http(order_url + "/" + order_id, method="PATCH", json={"status": "Refunded"})
    if updated_order["code"] not in range(200, 300):
        return jsonify({
            "code": updated_order["code"],
            "message": "Order status could not be updated after the refund.",
        }), updated_order["code"]

    notification_queued = True
    try:
        send_email(updated_order["data"])
    except Exception:
        logger.exception("Refund notification could not be queued")
        notification_queued = False
    return jsonify({
        "code": 200,
        "message": (
            "Refund processed and notification queued."
            if notification_queued
            else "Refund processed; notification could not be queued."
        ),
    }), 200

def send_email(order_details):
    email_order = dict(order_details)
    amqp_setup.check_setup()
    email_order["type"] = "order_refund"
    amqp_setup.channel.basic_publish(exchange="email_exchange", routing_key="confirmation.email",
                                     body=json.dumps(email_order), properties=pika.BasicProperties(delivery_mode=2))
    

if __name__ == "__main__":
    port = int(environ.get('PORT', 5700))
    debug = environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host="0.0.0.0", port=port, debug=debug)
