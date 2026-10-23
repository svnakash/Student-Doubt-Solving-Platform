
from flask import Flask, app, jsonify
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

from app.config import Config
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
)

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "SECRET_KEY must be configured before starting the application."
        )

    if not app.config.get("JWT_SECRET_KEY"):
        app.config["JWT_SECRET_KEY"] = app.config["SECRET_KEY"]

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    # Import models after initializing the extensions.
    with app.app_context():
        from app import models

    # Import and register blueprints inside the app factory
    # to avoid circular imports.
    from app.routes.auth import auth_bp
    from app.routes.verification import verification_bp
    from app.routes.questions import questions_bp
    from app.routes.answers import answers_bp

    app.register_blueprint(
        auth_bp,
        url_prefix="/api/v1/auth",
    )

    app.register_blueprint(
        verification_bp,
        url_prefix="/api/v1/verification",
    )
    app.register_blueprint(
        questions_bp,
        url_prefix="/api/v1/questions",
    )
    app.register_blueprint(
        answers_bp,
        url_prefix="/api/v1/questions",
    )
    @app.get("/api/health")
    def health_check():
        try:
            db.session.execute(db.text("SELECT 1"))
        except Exception:
            app.logger.exception("Database health check failed")
            return jsonify({
                "success": False,
                "error": {
                    "code": "DATABASE_UNAVAILABLE",
                    "message": "The service is temporarily unavailable.",
                },
            }), 503

        return jsonify({
            "success": True,
            "data": {
                "status": "healthy",
                "database": "connected",
                "service": "student-doubt-solving-backend",
            },
        }), 200

    return app
