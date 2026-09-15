from .conftest import load_module


def test_item_constructor_keeps_scalar_values_and_category_filter_works(monkeypatch):
    catalogue = load_module(
        "catalogue_service",
        "microservices/simple/catalogue/src/catalogue.py",
        monkeypatch,
        "CATALOGUE_DATABASE_URL",
    )
    with catalogue.app.app_context():
        catalogue.db.create_all()
        catalogue.db.session.add(catalogue.Item(
            "i01", "Food", "Chicken Rice", 5.00, "image", "description", 0, 0
        ))
        catalogue.db.session.commit()

    response = catalogue.app.test_client().get("/api/v1/catalogue?category=Food")
    assert response.status_code == 200
    assert response.get_json()["data"]["items"][0]["item_id"] == "i01"


def test_catalogue_rating_rejects_invalid_values(monkeypatch):
    catalogue = load_module(
        "catalogue_service_validation",
        "microservices/simple/catalogue/src/catalogue.py",
        monkeypatch,
        "CATALOGUE_DATABASE_URL",
    )
    response = catalogue.app.test_client().patch(
        "/api/v1/catalogue/i01/rating",
        json={"rating": 6, "review_count": 1},
    )
    assert response.status_code == 400
