import pytest

from .conftest import load_module


def test_order_builder_calculates_prices_from_service_data():
    builder = load_module(
        "order_builder_service",
        "microservices/complex/process_order/src/order_builder.py",
    )

    order = builder.build_authoritative_order(
        {
            "user_id": "user@example.com",
            "token": "tok_test",
            "delivery_address": "Address",
            "delivery_datetime": "2026-09-16",
        },
        fetch_cart=lambda user_id: {"code": 200, "data": {
            "cart_items": [{"item_id": "i01", "quantity": 2}],
            "cart_venues": [{"venue_id": "v01", "datetime": "2026-09-16 18:00"}],
        }},
        fetch_catalogue_item=lambda item_id: {"code": 200, "data": {
            "item_id": item_id, "item_name": "Item", "item_price": "6.17",
        }},
        fetch_venue=lambda venue_id: {"code": 200, "data": {
            "venue_id": venue_id, "venue_name": "Venue", "venue_price": "5.00",
        }},
    )

    assert order["total_amount"] == "17.34"
    assert order["order_items"][0]["item_price"] == "6.17"
    assert order["venue"]["venue_price"] == "5.00"


def test_order_builder_rejects_an_empty_cart():
    builder = load_module(
        "order_builder_empty_cart",
        "microservices/complex/process_order/src/order_builder.py",
    )

    with pytest.raises(builder.OrderBuildError) as error:
        builder.build_authoritative_order(
            {
                "user_id": "user@example.com",
                "token": "tok_test",
                "delivery_address": "Address",
                "delivery_datetime": "2026-09-16",
            },
            fetch_cart=lambda user_id: {"code": 200, "data": {"cart_items": [], "cart_venues": []}},
            fetch_catalogue_item=lambda item_id: None,
            fetch_venue=lambda venue_id: None,
        )

    assert error.value.status_code == 400
