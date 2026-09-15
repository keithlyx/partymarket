from .conftest import load_module


def valid_order():
    return {
        "user_id": "user@example.com",
        "token": "tok_test",
        "idempotency_key": "checkout-123",
        "delivery_address": "Address",
        "delivery_datetime": "2026-09-16",
        # These fields represent a tampered browser payload and must be ignored.
        "total_amount": "999.99",
        "items": [{"item_id": "i01", "item_quantity": 1, "item_price": "999.99"}],
    }


def test_process_order_converts_decimal_total_to_exact_cents(monkeypatch):
    process_order = load_module(
        "process_order_service",
        "microservices/complex/process_order/src/process_order.py",
    )
    calls = []

    def fake_invoke(url, method="GET", json=None, **kwargs):
        calls.append((url, method, json))
        if method == "GET" and "/carts/" in url:
            return {"code": 200, "data": {"cart_items": [{"item_id": "i01", "quantity": 2}], "cart_venues": []}}
        if method == "GET" and "/catalogue/" in url:
            return {"code": 200, "data": {"item_id": "i01", "item_name": "Chicken rice", "item_price": "6.17"}}
        if "payments" in url:
            return {"code": 200, "order_id": "ch_123", "receipt_url": "receipt"}
        if method == "DELETE":
            return {"code": 200}
        return {"code": 201}

    monkeypatch.setattr(process_order, "invoke_http", fake_invoke)
    monkeypatch.setattr(process_order, "send_email", lambda order: None)

    response = process_order.app.test_client().post("/api/v1/orders", json=valid_order())
    assert response.status_code == 201
    payment_payload = next(call[2] for call in calls if call[1] == "POST" and "payments" in call[0])
    assert payment_payload["amount_cents"] == 1234
    assert payment_payload["idempotency_key"] == "checkout-123"
    order_payload = next(call[2] for call in calls if call[1] == "POST" and "/orders" in call[0])
    assert order_payload["total_amount"] == "12.34"
    assert order_payload["order_items"][0]["item_name"] == "Chicken rice"
    assert order_payload["order_items"][0]["item_price"] == "6.17"


def test_process_order_reverses_payment_when_order_storage_fails(monkeypatch):
    process_order = load_module(
        "process_order_service_compensation",
        "microservices/complex/process_order/src/process_order.py",
    )
    calls = []

    def fake_invoke(url, method="GET", json=None, **kwargs):
        calls.append((url, method, json))
        if method == "GET" and "/carts/" in url:
            return {"code": 200, "data": {"cart_items": [{"item_id": "i01", "quantity": 1}], "cart_venues": []}}
        if method == "GET" and "/catalogue/" in url:
            return {"code": 200, "data": {"item_price": "12.34"}}
        if "payments" in url:
            return {"code": 200, "order_id": "ch_123", "receipt_url": "receipt"}
        if "refunds" in url:
            return {"code": 200, "refund_id": "re_123"}
        return {"code": 500, "message": "storage failed"}

    monkeypatch.setattr(process_order, "invoke_http", fake_invoke)
    response = process_order.app.test_client().post(
        "/api/v1/orders",
        json={
            "user_id": "user@example.com",
            "token": "tok_test",
            "idempotency_key": "checkout-123",
            "delivery_address": "Address",
            "delivery_datetime": "2026-09-16",
        },
    )

    assert response.status_code == 502
    refund_call = next(call for call in calls if "refunds" in call[0])
    assert refund_call[2]["amount_cents"] == 1234


def test_process_order_rejects_missing_fields():
    process_order = load_module(
        "process_order_service_validation",
        "microservices/complex/process_order/src/process_order.py",
    )
    response = process_order.app.test_client().post(
        "/api/v1/orders",
        json={"user_id": "user@example.com"},
    )
    assert response.status_code == 400


def test_process_order_returns_payment_failure_without_storing_order(monkeypatch):
    process_order = load_module(
        "process_order_service_payment_failure",
        "microservices/complex/process_order/src/process_order.py",
    )
    calls = []

    def fake_invoke(url, method="GET", json=None, **kwargs):
        calls.append((url, method, json))
        if method == "GET" and "/carts/" in url:
            return {"code": 200, "data": {"cart_items": [{"item_id": "i01", "quantity": 1}], "cart_venues": []}}
        if method == "GET" and "/catalogue/" in url:
            return {"code": 200, "data": {"item_price": "12.34"}}
        if "payments" in url:
            return {"code": 402, "message": "card declined"}
        raise AssertionError(f"Unexpected downstream call: {method} {url}")

    monkeypatch.setattr(process_order, "invoke_http", fake_invoke)
    response = process_order.app.test_client().post(
        "/api/v1/orders",
        json=valid_order(),
    )

    assert response.status_code == 402
    assert not any(method == "POST" and "/orders" in url for url, method, _ in calls)


def test_process_order_rejects_incomplete_payment_response(monkeypatch):
    process_order = load_module(
        "process_order_service_incomplete_payment",
        "microservices/complex/process_order/src/process_order.py",
    )

    def fake_invoke(url, method="GET", json=None, **kwargs):
        if method == "GET" and "/carts/" in url:
            return {"code": 200, "data": {"cart_items": [{"item_id": "i01", "quantity": 1}], "cart_venues": []}}
        if method == "GET" and "/catalogue/" in url:
            return {"code": 200, "data": {"item_price": "12.34"}}
        if "payments" in url:
            return {"code": 200, "receipt_url": "receipt"}
        raise AssertionError(f"Unexpected downstream call: {method} {url}")

    monkeypatch.setattr(process_order, "invoke_http", fake_invoke)
    response = process_order.app.test_client().post(
        "/api/v1/orders",
        json=valid_order(),
    )

    assert response.status_code == 502
