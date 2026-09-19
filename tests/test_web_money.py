import sys
from decimal import Decimal

import pytest

from .conftest import load_module
from .test_auth import _create_user, _load_user_application


def _load_common(monkeypatch, tmp_path):
    for module_name in list(sys.modules):
        if module_name == "user_application" or module_name.startswith("user_application."):
            sys.modules.pop(module_name)

    monkeypatch.setenv("USER_DATABASE_URL", f"sqlite:///{(tmp_path / 'users.db').as_posix()}")
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret")
    load_module("user_application", "main/user_application/__init__.py", monkeypatch=monkeypatch)
    return load_module("web_common", "main/user_application/route_modules/common.py")


def test_invalid_money_is_not_converted_to_zero(monkeypatch, tmp_path):
    common = _load_common(monkeypatch, tmp_path)

    with pytest.raises(ValueError):
        common.as_money("not-a-price")


def test_non_finite_money_is_rejected(monkeypatch, tmp_path):
    common = _load_common(monkeypatch, tmp_path)

    with pytest.raises(ValueError):
        common.as_money("NaN")


def test_valid_money_remains_decimal(monkeypatch, tmp_path):
    common = _load_common(monkeypatch, tmp_path)

    assert common.as_money("12.30") == Decimal("12.30")


def test_cart_invalid_money_redirects_with_controlled_error(monkeypatch, tmp_path):
    app_module = _load_user_application(monkeypatch, tmp_path)
    _create_user(app_module)
    client = app_module.app.test_client()
    client.post(
        "/login",
        data={"username": "keith", "password": "correct-password"},
    )

    from user_application.route_modules import cart as cart_routes

    def fake_invoke(url, method="GET", **kwargs):
        if url == cart_routes.CART_URL + "/api/v1/carts/keith@example.com":
            return {"data": {"cart_items": [{"item_id": "i01", "quantity": 1}], "cart_venues": []}}
        return {"data": {"item_price": "not-a-price", "item_img": "", "item_name": "Item"}}

    monkeypatch.setattr(cart_routes, "invoke_http", fake_invoke)

    response = client.get("/cart")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_order_details_invalid_money_redirects_with_controlled_error(monkeypatch, tmp_path):
    app_module = _load_user_application(monkeypatch, tmp_path)
    _create_user(app_module)
    client = app_module.app.test_client()
    client.post(
        "/login",
        data={"username": "keith", "password": "correct-password"},
    )

    from user_application.route_modules import orders as order_routes

    def fake_invoke(url, method="GET", **kwargs):
        if url == order_routes.VIEW_ORDER_URL + "/api/v1/orders/order-1":
            return {
                "code": 200,
                "data": {
                    "order": {
                        "order_id": "order-1",
                        "user_id": "keith@example.com",
                        "total_amount": "12.30",
                        "order_items": [{"item_id": "i01", "item_price": "not-a-price"}],
                    },
                },
            }
        return {"code": 200, "data": {"reviews": []}}

    monkeypatch.setattr(order_routes, "invoke_http", fake_invoke)

    response = client.get("/order-logs/order-1")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/order-logs")
