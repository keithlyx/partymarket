from .conftest import load_module


def valid_order():
    return {
        "user_id": "user@example.com",
        "total_amount": "12.34",
        "token": "tok_test",
        "delivery_address": "Address",
        "delivery_datetime": "2026-09-16",
        "items": [{"item_id": "i01", "item_quantity": 1, "item_price": "12.34"}],
    }


def test_process_order_converts_decimal_total_to_exact_cents(monkeypatch):
    process_order = load_module(
        "process_order_service",
        "microservices/complex/process_order/src/process_order.py",
    )
    calls = []

    def fake_invoke(url, method="GET", json=None, **kwargs):
        calls.append((url, method, json))
        if "payments" in url:
            return {"code": 200, "order_id": "ch_123", "receipt_url": "receipt"}
        if method == "DELETE":
            return {"code": 200}
        return {"code": 201}

    monkeypatch.setattr(process_order, "invoke_http", fake_invoke)
    monkeypatch.setattr(process_order, "send_email", lambda order: None)

    response = process_order.app.test_client().post("/api/v1/orders", json=valid_order())
    assert response.status_code == 201
    assert calls[0][2]["amount_cents"] == 1234


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
