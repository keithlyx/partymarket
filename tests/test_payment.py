from .conftest import load_module


def test_payment_sends_integer_cents_and_does_not_log_token(monkeypatch, caplog):
    payment = load_module(
        "payment_service",
        "microservices/simple/payment/src/payment.py",
    )
    captured = {}

    class FakeCharge(dict):
        pass

    def fake_charge_create(**kwargs):
        captured.update(kwargs)
        return FakeCharge(id="ch_123", receipt_url="https://example.test/receipt")

    monkeypatch.setattr(payment.stripe.Charge, "create", fake_charge_create)
    response = payment.app.test_client().post(
        "/api/v1/payments",
        json={"token": "tok_secret_test", "amount_cents": 1234},
    )

    assert response.status_code == 200
    assert captured["amount"] == 1234
    assert "tok_secret_test" not in caplog.text


def test_payment_rejects_dollar_amounts_at_the_boundary():
    payment = load_module(
        "payment_service_validation",
        "microservices/simple/payment/src/payment.py",
    )
    response = payment.app.test_client().post(
        "/api/v1/payments",
        json={"token": "tok_test", "amount": 12.34},
    )
    assert response.status_code == 400
