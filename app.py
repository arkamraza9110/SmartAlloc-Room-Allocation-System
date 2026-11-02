"""SmartAlloc Flask application entry point."""

from flask import Flask, render_template
from flask_cors import CORS

from config import Config
from models.database import db
from routes.allocation_routes import allocation_bp
from routes.class_routes import class_bp
from routes.dashboard_routes import dashboard_bp
from routes.demo_routes import demo_bp, ensure_demo_data
from routes.group_routes import group_bp
from routes.report_routes import report_bp
from routes.room_routes import room_bp
from routes.seat_routes import seat_bp
from routes.student_routes import student_bp


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)
    CORS(app)

    app.register_blueprint(student_bp)
    app.register_blueprint(class_bp)
    app.register_blueprint(group_bp)
    app.register_blueprint(room_bp)
    app.register_blueprint(seat_bp)
    app.register_blueprint(allocation_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(demo_bp)

    @app.before_request
    def seed_first_run():
        if not app.config.get("_demo_checked"):
            ensure_demo_data()
            app.config["_demo_checked"] = True

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/health")
    def health():
        health_data = db.health()
        status = 200 if health_data.get("connected") else 503
        return {"success": health_data.get("connected", False), "message": "SmartAlloc health check", "data": health_data, "errors": [] if health_data.get("connected") else [health_data.get("error")]}, status

    @app.errorhandler(404)
    def not_found(error):
        if str(getattr(error, "description", "")).startswith("/api"):
            return {"success": False, "message": "Endpoint not found", "data": {}, "errors": [str(error)]}, 404
        return error

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=Config.FLASK_ENV == "development")

