from .conftest import load_module


def test_missing_order_returns_not_found(monkeypatch):
    order = load_module(
        "order_service_missing",
        "microservices/simple/order/src/order.py",
        monkeypatch,
        "ORDER_DATABASE_URL",
    )
    with order.app.app_context():
        order.db.create_all()

    response = order.app.test_client().get("/api/v1/orders/missing")
    assert response.status_code == 404
    assert response.get_json()["code"] == 404


def test_order_creation_rejects_malformed_payload(monkeypatch):
    order = load_module(
        "order_service_validation",
        "microservices/simple/order/src/order.py",
        monkeypatch,
        "ORDER_DATABASE_URL",
    )
    response = order.app.test_client().post("/api/v1/orders", json={"order_id": "o01"})
    assert response.status_code == 400


def test_order_creation_serializes_decimal_money(monkeypatch):
    order = load_module(
        "order_service_create",
        "microservices/simple/order/src/order.py",
        monkeypatch,
        "ORDER_DATABASE_URL",
    )
    with order.app.app_context():
        order.db.create_all()

    response = order.app.test_client().post(
        "/api/v1/orders",
        json={
            "order_id": "o01",
            "user_id": "user@example.com",
            "total_amount": "12.30",
            "order_datetime": "2026-09-15T12:00:00",
            "delivery_address": "Address",
            "delivery_datetime": "2026-09-16",
            "order_items": [{"item_id": "i01", "item_quantity": 1, "item_price": "12.30"}],
        },
    )
    assert response.status_code == 201
    assert response.get_json()["data"]["total_amount"] == "12.30"
