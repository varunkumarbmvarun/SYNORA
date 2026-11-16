from flask import Blueprint, request, Response
from backend.database import db_session
from backend.services.report_service import ReportService
from backend.routes.utils import success_response, error_response

reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')


@reports_bp.route('/summary', methods=['GET'])
def get_summary():
    session = db_session()
    stats = ReportService.get_summary_stats(session)
    return success_response(stats)


@reports_bp.route('/export', methods=['GET'])
def export_report():
    session = db_session()
    report_type = request.args.get('type', 'students').lower()
    fmt = request.args.get('format', 'csv').lower()

    allowed_types = ['students', 'professors', 'courses', 'departments', 'facts', 'inference', 'queries']
    if report_type not in allowed_types:
        return error_response(f"Invalid report type '{report_type}'. Allowed: {allowed_types}", status_code=400)

    if fmt == 'pdf':
        try:
            pdf_bytes = ReportService.export_pdf(session, report_type)
            return Response(
                pdf_bytes,
                mimetype="application/pdf",
                headers={"Content-disposition": f"attachment; filename={report_type}_report.pdf"}
            )
        except Exception as e:
            return error_response(f"PDF generation failed: {str(e)}", status_code=500)
    elif fmt == 'csv':
        csv_str = ReportService.export_csv(session, report_type)
        return Response(
            csv_str,
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={report_type}_report.csv"}
        )
    else:
        return error_response(f"Invalid format '{fmt}'. Allowed: csv, pdf", status_code=400)
