from .conftest import load_module


def _order_response():
    return {
        "code": 200,
        "user_id": "user@example.com",
        "order": {
            "order_id": "ch_123",
            "user_id": "user@example.com",
            "total_amount": "25.00",
            "order_datetime": "2026-09-15T12:00:00",
            "order_status": "Accepted",
            "delivery_address": "Address",
            "delivery_datetime": "2026-09-16",
            "order_items": [{
                "item_id": "i01",
                "item_quantity": 2,
                "item_price": "10.00",
            }],
            "venue": {
                "venue_id": "v01",
                "venue_price": "5.00",
                "venue_datetime": "2026-09-16 18:00",
            },
        },
    }


def test_single_order_uses_consistent_envelope_and_preserves_paid_values(monkeypatch):
    view_order = load_module(
        "view_order_service_single",
        "microservices/complex/view_order/src/view_order.py",
    )

    def fake_invoke(url, method="GET", **kwargs):
        if url.endswith("/ch_123"):
            return _order_response()
        if "/catalogue/i01" in url:
            return {"code": 200, "data": {"item_id": "i01", "item_name": "Current name", "item_price": "99.00"}}
        if "/venues/v01" in url:
            return {"code": 200, "data": {"venue_id": "v01", "venue_name": "Current venue", "venue_price": "99.00"}}
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(view_order, "invoke_http", fake_invoke)
    response = view_order.app.test_client().get("/api/v1/orders/ch_123")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["code"] == 200
    assert payload["data"]["order"]["user_id"] == "user@example.com"
    assert payload["data"]["order"]["order_items"][0]["item_price"] == "10.00"
    assert payload["data"]["order"]["venue"]["venue_price"] == "5.00"
    assert payload["data"]["order"]["venue"]["venue_datetime"] == "2026-09-16 18:00"


def test_order_list_is_keyed_by_order_id(monkeypatch):
    view_order = load_module(
        "view_order_service_list",
        "microservices/complex/view_order/src/view_order.py",
    )

    def fake_invoke(url, method="GET", **kwargs):
        if url.endswith("/orders"):
            return {"code": 200, "orders": [_order_response()["order"]]}
        if "/catalogue/i01" in url:
            return {"code": 200, "data": {"item_id": "i01", "item_name": "Item", "item_price": "10.00"}}
        if "/venues/v01" in url:
            return {"code": 200, "data": {"venue_id": "v01", "venue_name": "Venue", "venue_price": "5.00"}}
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(view_order, "invoke_http", fake_invoke)
    response = view_order.app.test_client().get(
        "/api/v1/orders?user_id=user@example.com"
    )

    assert response.status_code == 200
    assert list(response.get_json()["data"]["orders"]) == ["ch_123"]
