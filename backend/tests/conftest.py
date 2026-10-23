
import pytest

from app import create_app, db


@pytest.fixture
def app(tmp_path):
    test_db = tmp_path / "test.db"

    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-only-secret-key-at-least-32-bytes-long",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{test_db.as_posix()}",
    })

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
