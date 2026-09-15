from .conftest import load_module


def test_refund_uses_stored_amount_and_checks_owner(monkeypatch):
    process_refund = load_module(
        "process_refund_service",
        "microservices/complex/process_refund/src/process_refund.py",
    )
    calls = []

    def fake_invoke(url, method="GET", json=None, **kwargs):
        calls.append((url, method, json))
        if method == "GET":
            return {
                "code": 200,
                "order": {
                    "order_id": "ch_123",
                    "user_id": "user@example.com",
                    "total_amount": "12.34",
                    "order_status": "Accepted",
                },
            }
        if "refunds" in url:
            return {"code": 200, "refund_id": "re_123", "status": "succeeded"}
        return {"code": 200, "data": {"order_id": "ch_123", "user_id": "user@example.com"}}

    monkeypatch.setattr(process_refund, "invoke_http", fake_invoke)
    monkeypatch.setattr(process_refund, "send_email", lambda order: None)
    response = process_refund.app.test_client().post(
        "/api/v1/refunds",
        json={"order_id": "ch_123", "user_id": "user@example.com", "amount": "999.99"},
    )

    assert response.status_code == 200
    payment_call = next(call for call in calls if "refunds" in call[0])
    assert payment_call[2]["amount_cents"] == 1234


def test_refund_rejects_a_different_owner(monkeypatch):
    process_refund = load_module(
        "process_refund_service_owner",
        "microservices/complex/process_refund/src/process_refund.py",
    )
    monkeypatch.setattr(process_refund, "invoke_http", lambda *args, **kwargs: {
        "code": 200,
        "order": {
            "order_id": "ch_123",
            "user_id": "owner@example.com",
            "total_amount": "12.34",
            "order_status": "Accepted",
        },
    })

    response = process_refund.app.test_client().post(
        "/api/v1/refunds",
        json={"order_id": "ch_123", "user_id": "other@example.com"},
    )

    assert response.status_code == 403


def test_refund_rejects_orders_that_are_not_accepted(monkeypatch):
    process_refund = load_module(
        "process_refund_service_status",
        "microservices/complex/process_refund/src/process_refund.py",
    )
    monkeypatch.setattr(process_refund, "invoke_http", lambda *args, **kwargs: {
        "code": 200,
        "order": {
            "order_id": "ch_123",
            "user_id": "user@example.com",
            "total_amount": "12.34",
            "order_status": "Delivered",
        },
    })

    response = process_refund.app.test_client().post(
        "/api/v1/refunds",
        json={"order_id": "ch_123", "user_id": "user@example.com"},
    )

    assert response.status_code == 409
