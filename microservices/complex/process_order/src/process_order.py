import datetime
import json
import logging
from os import environ
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple, TypedDict

import pika
from flask import Flask, jsonify, request
from flask_cors import CORS

import amqp_setup
from invokes import invoke_http


class OrderItem(TypedDict):
    item_id: str
    item_quantity: int
    item_price: Any


class OrderRequest(TypedDict, total=False):
    user_id: str
    total_amount: float
    token: str
    delivery_address: str
    delivery_datetime: str
    items: List[OrderItem]
    venue: Dict[str, Any]


payment_url = environ.get("payment_URL") or "http://payment:5008/api/v1/payments"
cart_url = environ.get("cart_URL") or "http://cart:5005/api/v1/carts"
order_url = environ.get("order_URL") or "http://order:5006/api/v1/orders"

app = Flask(__name__)
CORS(app)
logger = logging.getLogger(__name__)


def _validate_order(data: Any) -> Optional[str]:
    if not isinstance(data, dict):
        return "Request payload must be a JSON object."

    required_fields = (
        "user_id",
        "total_amount",
        "token",
        "delivery_address",
        "delivery_datetime",
        "items",
    )
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return "Missing required order fields: " + ", ".join(missing_fields) + "."

    if not isinstance(data["user_id"], str) or not data["user_id"].strip():
        return "user_id must be a non-empty string."
    if not isinstance(data["token"], str) or not data["token"].strip():
        return "token must be a non-empty string."
    if not isinstance(data["delivery_address"], str) or not data["delivery_address"].strip():
        return "delivery_address must be a non-empty string."
    if not isinstance(data["delivery_datetime"], str) or not data["delivery_datetime"].strip():
        return "delivery_datetime must be a non-empty string."

    total_amount = data["total_amount"]
    try:
        parsed_total = Decimal(str(total_amount))
    except (InvalidOperation, ValueError):
        parsed_total = Decimal("-1")
    if isinstance(total_amount, bool) or not parsed_total.is_finite() or parsed_total < 0:
        return "total_amount must be a non-negative number."
    if parsed_total.as_tuple().exponent < -2:
        return "total_amount must have at most two decimal places."

    items = data["items"]
    if not isinstance(items, list):
        return "items must be a list."
    for item in items:
        if not isinstance(item, dict):
            return "Each order item must be a JSON object."
        if any(field not in item for field in ("item_id", "item_quantity", "item_price")):
            return "Each order item must include item_id, item_quantity, and item_price."
        if not isinstance(item["item_id"], str) or not item["item_id"].strip():
            return "Each item_id must be a non-empty string."
        if isinstance(item["item_quantity"], bool) or not isinstance(item["item_quantity"], int) or item["item_quantity"] < 1:
            return "Each item_quantity must be a positive integer."
        try:
            item_price = Decimal(str(item["item_price"]))
        except (InvalidOperation, ValueError):
            item_price = Decimal("-1")
        if isinstance(item["item_price"], bool) or not item_price.is_finite() or item_price < 0 or item_price.as_tuple().exponent < -2:
            return "Each item_price must be a non-negative number."

    venue = data.get("venue")
    if venue is not None:
        if not isinstance(venue, dict) or any(field not in venue for field in ("venue_id", "venue_price", "venue_datetime")):
            return "venue must include venue_id, venue_price, and venue_datetime."

    return None


def _downstream_error(response: Dict[str, Any], message: str) -> Tuple[Any, int]:
    code = response.get("code", 502)
    if code >= 500:
        code = 502
    return jsonify({"code": code, "message": message}), code


@app.route("/api/v1/orders", methods=["POST"])
def create_order():
    order = request.get_json(silent=True)
    validation_error = _validate_order(order)
    if validation_error:
        return jsonify({"code": 400, "message": validation_error}), 400

    try:
        return process_order(order)
    except Exception:
        logger.exception("Unexpected order orchestration failure")
        return jsonify({
            "code": 500,
            "message": "An unexpected error occurred while processing the order.",
        }), 500


def process_order(order: OrderRequest):
    amount_cents = int(Decimal(str(order["total_amount"])) * 100)
    payment = invoke_http(
        payment_url,
        method="POST",
        json={"token": order["token"], "amount_cents": amount_cents},
    )
    if payment.get("code") not in range(200, 300):
        return _downstream_error(payment, "Payment could not be completed.")

    order_id = payment.get("order_id")
    receipt_url = payment.get("receipt_url")
    if not order_id or not receipt_url:
        return jsonify({
            "code": 502,
            "message": "Payment service returned an incomplete response.",
        }), 502

    order_for_service = dict(order)
    order_for_service["order_id"] = order_id
    order_for_service["order_datetime"] = datetime.datetime.now().isoformat()
    order_for_service["order_items"] = order_for_service.pop("items")
    order_for_service["receipt_url"] = receipt_url
    order_for_service.pop("token", None)

    result = invoke_http(order_url, method="POST", json=order_for_service)
    if result.get("code") not in range(200, 300):
        return _downstream_error(result, "Order could not be stored.")

    send_email(order_for_service)
    delete_status = invoke_http(cart_url + "/" + order["user_id"], method="DELETE")
    if delete_status.get("code") not in range(200, 300):
        return _downstream_error(delete_status, "Order was created but the cart could not be cleared.")

    return jsonify({
        "code": 201,
        "message": "Order created successfully.",
        "order_id": order_id,
    }), 201


def send_email(order: Dict[str, Any]) -> None:
    email_order = dict(order)
    email_order["type"] = "order_confirmation"
    amqp_setup.check_setup()
    amqp_setup.channel.basic_publish(
        exchange="email_exchange",
        routing_key="confirmation.email",
        body=json.dumps(email_order),
        properties=pika.BasicProperties(delivery_mode=2),
    )


if __name__ == "__main__":
    port = int(environ.get("PORT", 5200))
    app.run(host="0.0.0.0", port=port)
