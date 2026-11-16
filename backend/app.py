import os
import sys
import logging
from pathlib import Path

# Add project root to sys.path so 'backend' package resolves cleanly
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from flask import Flask, jsonify, request
from flask_cors import CORS
from backend.config import Config
from backend.database import db_session, init_db
from backend.seed import seed_database
from backend.routes.utils import success_response, error_response

# Import Blueprints
from backend.routes.students import students_bp
from backend.routes.professors import professors_bp
from backend.routes.courses import courses_bp
from backend.routes.departments import departments_bp
from backend.routes.facts import facts_bp
from backend.routes.rules import rules_bp
from backend.routes.inference import inference_bp
from backend.routes.query import query_bp
from backend.routes.graph import graph_bp
from backend.routes.dashboard import dashboard_bp
from backend.routes.reports import reports_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure Logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(Config.LOG_FILE, encoding='utf-8')
        ]
    )
    logger = logging.getLogger("CollegeKB")
    logger.info("Initializing College Knowledge Base REST API...")

    # CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Teardown database session
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    # Root route
    @app.route('/', methods=['GET'])
    def root_index():
        return jsonify({
            "service": "College Knowledge Base FOL API",
            "version": "1.0.0",
            "status": "online",
            "frontend_ui": "http://localhost:8501",
            "message": "Flask REST API is online. Please open the Streamlit UI at http://localhost:8501",
            "endpoints": [
                "/api/health", "/api/dashboard/stats", "/api/students",
                "/api/professors", "/api/courses", "/api/departments",
                "/api/facts", "/api/rules", "/api/inference/forward",
                "/api/inference/backward", "/api/query", "/api/knowledge-graph",
                "/api/reports/summary"
            ]
        })

    # Health Check
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return success_response({
            "status": "healthy",
            "service": "College Knowledge Base FOL API",
            "version": "1.0.0"
        }, message="Backend service is operational")

    # Centralized Error Handlers
    @app.errorhandler(400)
    def bad_request(e):
        return error_response("Bad request", code="BAD_REQUEST", details=str(e), status_code=400)

    @app.errorhandler(404)
    def not_found(e):
        return error_response("Endpoint or resource not found", code="NOT_FOUND", details=str(e), status_code=404)

    @app.errorhandler(422)
    def unprocessable_entity(e):
        return error_response("Unprocessable entity / parse failure", code="UNPROCESSABLE", details=str(e), status_code=422)

    @app.errorhandler(500)
    def internal_server_error(e):
        logger.error(f"Internal server error: {e}", exc_info=True)
        return error_response("Internal server error", code="INTERNAL_ERROR", details=str(e), status_code=500)

    # Register Blueprints
    app.register_blueprint(students_bp)
    app.register_blueprint(professors_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(departments_bp)
    app.register_blueprint(facts_bp)
    app.register_blueprint(rules_bp)
    app.register_blueprint(inference_bp)
    app.register_blueprint(query_bp)
    app.register_blueprint(graph_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(reports_bp)

    # Initialize DB & Seed on startup
    with app.app_context():
        init_db()
        try:
            seed_database(session=db_session(), force_reset=False)
        except Exception as e:
            logger.error(f"Database seed check failed: {e}")

    return app


app = create_app()

if __name__ == "__main__":
    print(f"Starting College Knowledge Base API on {Config.HOST}:{Config.PORT}...")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
