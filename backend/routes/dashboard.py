from flask import Blueprint
from backend.database import db_session
from backend.models import (
    Student, Professor, Course, Department, Fact, Rule,
    InferenceResult, QueryHistory, ActivityLog
)
from backend.services.report_service import ReportService
from backend.routes.utils import success_response

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    session = db_session()
    summary = ReportService.get_summary_stats(session)

    # Recent activities
    recent_activities = session.query(ActivityLog).order_by(ActivityLog.id.desc()).limit(10).all()

    # Recent facts
    recent_facts = session.query(Fact).order_by(Fact.id.desc()).limit(10).all()

    # Recent queries
    recent_queries = session.query(QueryHistory).order_by(QueryHistory.id.desc()).limit(5).all()

    # Last inference run
    last_inf = session.query(InferenceResult).order_by(InferenceResult.id.desc()).first()

    payload = {
        **summary,
        "recent_activities": [a.to_dict() for a in recent_activities],
        "recent_facts": [f.to_dict() for f in recent_facts],
        "recent_queries": [q.to_dict() for q in recent_queries],
        "last_inference_run": last_inf.to_dict() if last_inf else None,
        "system_status": {
            "api": "healthy",
            "database": "connected",
            "rules_enabled": summary["enabled_rules_count"],
            "total_rules": summary["rules_count"]
        }
    }

    return success_response(payload)
