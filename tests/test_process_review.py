from .conftest import load_module


def test_create_review_rolls_back_when_rating_update_fails(monkeypatch):
    process_review = load_module(
        "process_review_service_create_compensation",
        "microservices/complex/process_review/src/process_review.py",
    )
    calls = []

    def fake_invoke(url, method="GET", json=None, **kwargs):
        calls.append((url, method, json, kwargs))
        if method == "POST" and url.endswith("/reviews"):
            return {"code": 201, "data": {"user_id": "user@example.com"}}
        if method == "GET":
            return {"code": 200, "data": {"reviews": [{"rating": 5}]}}
        if method == "PATCH" and "/catalogue/" in url:
            return {"code": 503, "message": "catalogue unavailable"}
        if method == "DELETE":
            return {"code": 200, "message": "Review deleted."}
        raise AssertionError(f"Unexpected downstream call: {method} {url}")

    monkeypatch.setattr(process_review, "invoke_http", fake_invoke)
    response = process_review.app.test_client().post(
        "/api/v1/reviews",
        json={
            "user_id": "user@example.com",
            "prod_id": "i01",
            "rating": 5,
            "rating_desc": "Good",
        },
    )

    assert response.status_code == 502
    assert any(method == "DELETE" for _, method, _, _ in calls)


def test_update_review_restores_previous_value_when_rating_update_fails(monkeypatch):
    process_review = load_module(
        "process_review_service_update_compensation",
        "microservices/complex/process_review/src/process_review.py",
    )
    calls = []

    def fake_invoke(url, method="GET", json=None, **kwargs):
        calls.append((url, method, json, kwargs))
        if method == "GET" and url.endswith("/reviews/user@example.com/i01"):
            return {
                "code": 200,
                "data": {
                    "user_id": "user@example.com",
                    "prod_id": "i01",
                    "rating": 3,
                    "rating_desc": "Previous",
                },
            }
        if method == "PATCH" and url.endswith("/reviews/user@example.com/i01"):
            return {"code": 200, "data": {"rating": json["rating"]}}
        if method == "GET":
            return {"code": 200, "data": {"reviews": [{"rating": 4}]}}
        if method == "PATCH" and "/catalogue/" in url:
            return {"code": 503, "message": "catalogue unavailable"}
        raise AssertionError(f"Unexpected downstream call: {method} {url}")

    monkeypatch.setattr(process_review, "invoke_http", fake_invoke)
    response = process_review.app.test_client().patch(
        "/api/v1/reviews/user@example.com/i01",
        json={"rating": 4, "rating_desc": "Updated"},
    )

    assert response.status_code == 502
    rollback_calls = [
        call for call in calls
        if call[1] == "PATCH" and call[0].endswith("/reviews/user@example.com/i01")
    ]
    assert rollback_calls[-1][2]["rating"] == 3


def test_update_review_rejects_unknown_product_type():
    process_review = load_module(
        "process_review_service_product_validation",
        "microservices/complex/process_review/src/process_review.py",
    )
    response = process_review.app.test_client().patch(
        "/api/v1/reviews/user@example.com/x01",
        json={"rating": 4, "rating_desc": "Updated"},
    )

    assert response.status_code == 400
