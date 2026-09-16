from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Dict, Mapping


class OrderBuildError(Exception):
    """A cart or catalogue response cannot be turned into an order."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _require_success(response: Any, service_name: str) -> Mapping[str, Any]:
    if not isinstance(response, dict):
        raise OrderBuildError(f"{service_name} service returned invalid data.")

    code = response.get("code")
    if not isinstance(code, int) or code not in range(200, 300):
        raise OrderBuildError(f"{service_name} data could not be retrieved.", 502)
    return response


def _parse_price(value: Any, field_name: str) -> Decimal:
    try:
        price = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise OrderBuildError(f"Service returned an invalid {field_name}.")

    if not price.is_finite() or price < 0 or price.as_tuple().exponent < -2:
        raise OrderBuildError(f"Service returned an invalid {field_name}.")
    return price


def build_authoritative_order(
    checkout_request: Mapping[str, str],
    fetch_cart: Callable[[str], Any],
    fetch_catalogue_item: Callable[[str], Any],
    fetch_venue: Callable[[str], Any],
) -> Dict[str, Any]:
    """Build order data from server-owned cart and catalogue values."""
    user_id = checkout_request["user_id"]
    cart_response = _require_success(fetch_cart(user_id), "Cart")
    cart_data = cart_response.get("data")
    if not isinstance(cart_data, dict):
        raise OrderBuildError("Cart service returned invalid data.")

    cart_items = cart_data.get("cart_items", [])
    cart_venues = cart_data.get("cart_venues", [])
    if not isinstance(cart_items, list) or not isinstance(cart_venues, list):
        raise OrderBuildError("Cart service returned invalid data.")
    if not cart_items and not cart_venues:
        raise OrderBuildError("Cannot create an order from an empty cart.", 400)

    total_amount = Decimal("0.00")
    order_items = []
    for cart_item in cart_items:
        item_id = cart_item.get("item_id")
        quantity = cart_item.get("quantity")
        if not isinstance(item_id, str) or not item_id.strip() or not isinstance(quantity, int) or quantity < 1:
            raise OrderBuildError("Cart service returned invalid item data.")

        item_response = _require_success(fetch_catalogue_item(item_id), "Catalogue")
        item_data = item_response.get("data")
        if not isinstance(item_data, dict):
            raise OrderBuildError("Catalogue service returned invalid item data.")

        item_price = _parse_price(item_data.get("item_price"), "item price")
        total_amount += item_price * quantity
        order_items.append({
            "item_id": item_id,
            "item_name": item_data.get("item_name", item_id),
            "item_quantity": quantity,
            "item_price": f"{item_price:.2f}",
        })

    venue = None
    if cart_venues:
        cart_venue = cart_venues[0]
        venue_id = cart_venue.get("venue_id")
        venue_datetime = cart_venue.get("datetime")
        if not isinstance(venue_id, str) or not venue_id.strip() or not isinstance(venue_datetime, str) or not venue_datetime.strip():
            raise OrderBuildError("Cart service returned invalid venue data.")

        venue_response = _require_success(fetch_venue(venue_id), "Venue")
        venue_data = venue_response.get("data")
        if not isinstance(venue_data, dict):
            raise OrderBuildError("Venue service returned invalid venue data.")

        venue_price = _parse_price(venue_data.get("venue_price"), "venue price")
        total_amount += venue_price
        venue = {
            "venue_id": venue_id,
            "venue_name": venue_data.get("venue_name", venue_id),
            "venue_price": f"{venue_price:.2f}",
            "venue_datetime": venue_datetime,
        }

    return {
        "user_id": user_id,
        "total_amount": f"{total_amount:.2f}",
        "token": checkout_request["token"],
        "delivery_address": checkout_request["delivery_address"],
        "delivery_datetime": checkout_request["delivery_datetime"],
        "order_items": order_items,
        **({"venue": venue} if venue else {}),
    }
