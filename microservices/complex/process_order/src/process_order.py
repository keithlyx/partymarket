import datetime
import json
import logging
import uuid
from os import environ
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple, TypedDict

import pika
from flask import Flask, jsonify, request

import amqp_setup
from invokes import invoke_http


class OrderItem(TypedDict):
    item_id: str
    item_quantity: int
    item_price: Any


class OrderRequest(TypedDict, total=False):
    user_id: str
    token: str
    idempotency_key: str
    delivery_address: str
    delivery_datetime: str


payment_url = environ.get("PAYMENT_URL") or "http://payment:5008/api/v1/payments"
cart_url = environ.get("CART_URL") or "http://cart:5005/api/v1/carts"
order_url = environ.get("ORDER_URL") or "http://order:5006/api/v1/orders"
refund_url = environ.get("REFUND_URL") or "http://payment:5008/api/v1/refunds"
catalogue_url = environ.get("CATALOGUE_URL") or "http://catalogue:5004/api/v1/catalogue"
venue_url = environ.get("VENUE_URL") or "http://venue:5003/api/v1/venues"

app = Flask(__name__)
logger = logging.getLogger(__name__)


def _validate_order(data: Any) -> Optional[str]:
    if not isinstance(data, dict):
        return "Request payload must be a JSON object."

    required_fields = (
        "user_id",
        "token",
        "delivery_address",
        "delivery_datetime",
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
    if "idempotency_key" in data and (not isinstance(data["idempotency_key"], str) or not data["idempotency_key"].strip()):
        return "idempotency_key must be a non-empty string when provided."

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


def _build_authoritative_order(order: OrderRequest):
    """Build an order from cart and catalogue data instead of browser prices."""
    cart = invoke_http(cart_url + "/" + order["user_id"], method="GET")
    if cart.get("code") not in range(200, 300):
        return None, _downstream_error(cart, "Cart could not be retrieved.")

    cart_data = cart.get("data", {})
    cart_items = cart_data.get("cart_items", [])
    cart_venues = cart_data.get("cart_venues", [])
    if not cart_items and not cart_venues:
        return None, (jsonify({
            "code": 400,
            "message": "Cannot create an order from an empty cart.",
        }), 400)

    total_amount = Decimal("0.00")
    order_items = []
    for cart_item in cart_items:
        item_id = cart_item.get("item_id")
        quantity = cart_item.get("quantity")
        if not isinstance(item_id, str) or not item_id.strip() or not isinstance(quantity, int) or quantity < 1:
            return None, (jsonify({
                "code": 502,
                "message": "Cart service returned invalid item data.",
            }), 502)

        item_response = invoke_http(catalogue_url + "/" + item_id, method="GET")
        if item_response.get("code") not in range(200, 300):
            return None, _downstream_error(item_response, "Catalogue data could not be retrieved.")

        item_data = item_response.get("data", {})
        try:
            item_price = Decimal(str(item_data["item_price"]))
        except (KeyError, InvalidOperation, ValueError):
            return None, (jsonify({
                "code": 502,
                "message": "Catalogue service returned invalid price data.",
            }), 502)
        if not item_price.is_finite() or item_price < 0 or item_price.as_tuple().exponent < -2:
            return None, (jsonify({
                "code": 502,
                "message": "Catalogue service returned an invalid item price.",
            }), 502)

        total_amount += item_price * quantity
        order_items.append({
            "item_id": item_id,
            "item_quantity": quantity,
            "item_price": f"{item_price:.2f}",
        })

    venue = None
    if cart_venues:
        cart_venue = cart_venues[0]
        venue_id = cart_venue.get("venue_id")
        venue_datetime = cart_venue.get("datetime")
        if not isinstance(venue_id, str) or not venue_id.strip() or not isinstance(venue_datetime, str) or not venue_datetime.strip():
            return None, (jsonify({
                "code": 502,
                "message": "Cart service returned invalid venue data.",
            }), 502)

        venue_response = invoke_http(venue_url + "/" + venue_id, method="GET")
        if venue_response.get("code") not in range(200, 300):
            return None, _downstream_error(venue_response, "Venue data could not be retrieved.")

        venue_data = venue_response.get("data", {})
        try:
            venue_price = Decimal(str(venue_data["venue_price"]))
        except (KeyError, InvalidOperation, ValueError):
            return None, (jsonify({
                "code": 502,
                "message": "Venue service returned invalid price data.",
            }), 502)
        if not venue_price.is_finite() or venue_price < 0 or venue_price.as_tuple().exponent < -2:
            return None, (jsonify({
                "code": 502,
                "message": "Venue service returned an invalid venue price.",
            }), 502)

        total_amount += venue_price
        venue = {
            "venue_id": venue_id,
            "venue_price": f"{venue_price:.2f}",
            "venue_datetime": venue_datetime,
        }

    return {
        "user_id": order["user_id"],
        "total_amount": f"{total_amount:.2f}",
        "token": order["token"],
        "delivery_address": order["delivery_address"],
        "delivery_datetime": order["delivery_datetime"],
        "items": order_items,
        **({"venue": venue} if venue else {}),
    }, None


def process_order(order: OrderRequest):
    authoritative_order, error_response = _build_authoritative_order(order)
    if error_response:
        return error_response

    amount_cents = int(Decimal(authoritative_order["total_amount"]) * 100)
    idempotency_key = order.get("idempotency_key") or uuid.uuid4().hex
    payment = invoke_http(
        payment_url,
        method="POST",
        json={
            "token": order["token"],
            "amount_cents": amount_cents,
            "idempotency_key": idempotency_key,
        },
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

    order_for_service = dict(authoritative_order)
    order_for_service["order_id"] = order_id
    order_for_service["order_datetime"] = datetime.datetime.now().isoformat()
    order_for_service["order_items"] = order_for_service.pop("items")
    order_for_service["receipt_url"] = receipt_url
    order_for_service.pop("token", None)
    order_for_service.pop("idempotency_key", None)

    result = invoke_http(order_url, method="POST", json=order_for_service)
    if result.get("code") not in range(200, 300):
        if result.get("code") == 409:
            return jsonify({
                "code": 200,
                "message": "Order was already created.",
                "order_id": order_id,
            }), 200

        compensation = invoke_http(
            refund_url,
            method="POST",
            json={
                "charge_id": order_id,
                "amount_cents": amount_cents,
                "idempotency_key": idempotency_key + ":compensation",
            },
        )
        if compensation.get("code") not in range(200, 300):
            return jsonify({
                "code": 502,
                "message": "Order could not be stored and payment could not be reversed.",
            }), 502
        return _downstream_error(result, "Order could not be stored.")

    notification_queued = True
    try:
        send_email(order_for_service)
    except Exception:
        logger.exception("Order notification could not be queued")
        notification_queued = False

    delete_status = invoke_http(cart_url + "/" + order["user_id"], method="DELETE")
    if delete_status.get("code") not in range(200, 300):
        return _downstream_error(delete_status, "Order was created but the cart could not be cleared.")

    return jsonify({
        "code": 201,
        "message": (
            "Order created successfully."
            if notification_queued
            else "Order created successfully; notification could not be queued."
        ),
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
