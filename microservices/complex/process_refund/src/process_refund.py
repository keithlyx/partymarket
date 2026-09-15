from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from os import environ
from invokes import invoke_http
import amqp_setup
import pika
import json
import logging
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional

app = Flask(__name__)
logger = logging.getLogger(__name__)

payment_url = environ.get('PAYMENT_URL') or "http://payment:5008/api/v1/refunds"
order_url = environ.get('ORDER_URL') or "http://order:5006/api/v1/orders"
SUCCESS_CODES = range(200, 300)


@app.route('/api/v1/refunds', methods=["POST"])
def refund():
    data = request.get_json(silent=True)
    validation_error = _validate_request(data)
    if validation_error:
        return validation_error

    order_id = data["order_id"]
    user_id = data["user_id"]

    order_response = invoke_http(order_url + "/" + order_id, method="GET")
    if not _is_successful_response(order_response):
        return jsonify({
            "code": _response_code(order_response),
            "message": "Order could not be retrieved.",
        }), _response_code(order_response)

    order = order_response.get("order")
    if not isinstance(order, dict) or order.get("user_id") != user_id:
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

    amount_cents = _amount_in_cents(order)
    if amount_cents is None:
        return jsonify({
            "code": 502,
            "message": "Order service returned an invalid order amount.",
        }), 502

    data["amount_cents"] = amount_cents
    return process_refund(data)


def _validate_request(data: Any):
    if (not isinstance(data, dict) or not _non_empty_string(data.get("order_id"))
            or not _non_empty_string(data.get("user_id"))):
        return jsonify({
            "code": 400,
            "message": "Request must include order_id and user_id.",
        }), 400
    return None


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_successful_response(response: Any) -> bool:
    return isinstance(response, dict) and response.get("code") in SUCCESS_CODES


def _response_code(response: Any, default: int = 502) -> int:
    if isinstance(response, dict) and isinstance(response.get("code"), int):
        return response["code"]
    return default


def _amount_in_cents(order: Dict[str, Any]) -> Optional[int]:
    try:
        amount = Decimal(str(order["total_amount"]))
    except (KeyError, InvalidOperation, ValueError):
        return None
    if not amount.is_finite() or amount <= 0 or amount.as_tuple().exponent < -2:
        return None
    return int(amount * 100)


def process_refund(data: Dict[str, Any]):
    order_id = data["order_id"]
    refund_response = invoke_http(payment_url, method="POST", json={
        "charge_id": order_id,
        "amount_cents": data["amount_cents"],
        "idempotency_key": "refund:" + order_id,
    })
    if not _is_successful_response(refund_response):
        response_code = _response_code(refund_response)
        return jsonify({
            "code": response_code,
            "message": "Payment provider rejected the refund request.",
        }), response_code

    updated_order = invoke_http(order_url + "/" + order_id, method="PATCH", json={"status": "Refunded"})
    if not _is_successful_response(updated_order):
        response_code = _response_code(updated_order)
        return jsonify({
            "code": response_code,
            "message": "Order status could not be updated after the refund.",
        }), response_code

    notification_queued = True
    try:
        order_details = updated_order.get("data")
        if not isinstance(order_details, dict):
            raise ValueError("Order update response did not include order data.")
        send_email(order_details)
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
