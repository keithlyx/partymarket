import sys

from .conftest import load_module


def _load_user_application(monkeypatch, tmp_path):
    for module_name in list(sys.modules):
        if module_name == "user_application" or module_name.startswith("user_application."):
            sys.modules.pop(module_name)

    monkeypatch.setenv("USER_DATABASE_URL", f"sqlite:///{(tmp_path / 'users.db').as_posix()}")
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret")
    app_module = load_module(
        "user_application",
        "main/user_application/__init__.py",
        monkeypatch=monkeypatch,
    )
    app_module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    with app_module.app.app_context():
        app_module.db.create_all()
    return app_module


def _create_user(app_module, name="keith"):
    from user_application.models import Users

    user = Users(
        user_id_email=f"{name}@example.com",
        name=name,
        password=app_module.bcrypt.generate_password_hash("correct-password").decode("utf-8"),
    )
    with app_module.app.app_context():
        app_module.db.session.add(user)
        app_module.db.session.commit()


def test_username_is_case_insensitive_for_login(monkeypatch, tmp_path):
    app_module = _load_user_application(monkeypatch, tmp_path)
    _create_user(app_module)

    response = app_module.app.test_client().post(
        "/login",
        data={"username": "Keith", "password": "correct-password"},
    )

    assert response.status_code == 302


def test_registration_checks_normalized_username(monkeypatch, tmp_path):
    app_module = _load_user_application(monkeypatch, tmp_path)
    _create_user(app_module)

    response = app_module.app.test_client().post(
        "/register",
        data={
            "username": "Keith",
            "email": "another@example.com",
            "password": "correct-password",
            "confirm_password": "correct-password",
        },
    )

    assert response.status_code == 200
    assert b"username is taken" in response.data.lower()
