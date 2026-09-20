from .test_auth import _load_user_application


def test_catalogue_detail_is_public_read_only(monkeypatch, tmp_path):
    app_module = _load_user_application(monkeypatch, tmp_path)

    from user_application.route_modules import catalogue as catalogue_routes

    def fake_invoke(url, method="GET", **kwargs):
        if url == catalogue_routes.CATALOGUE_URL + "/api/v1/catalogue/i01":
            return {
                "data": {
                    "item_id": "i01",
                    "item_name": "Table",
                    "category_name": "Furniture",
                    "item_img": "",
                    "item_rating": "5.0",
                    "review_count": 0,
                    "item_price": "12.30",
                    "item_description": "A table",
                },
            }
        return {"data": {"reviews": []}}

    monkeypatch.setattr(catalogue_routes, "invoke_http", fake_invoke)

    response = app_module.app.test_client().get("/catalogue/i01")

    assert response.status_code == 200
    assert b"Table" in response.data


def test_catalogue_write_actions_still_require_login(monkeypatch, tmp_path):
    app_module = _load_user_application(monkeypatch, tmp_path)
    client = app_module.app.test_client()

    assert client.post("/add-to-cart/i01", data={"quantity": "1"}).status_code == 302
    assert client.post(
        "/add-review/i01",
        data={"rating": "5", "review": "Great"},
    ).status_code == 302
