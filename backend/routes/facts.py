from flask import Blueprint, request, Response
from backend.database import db_session
from backend.services.fact_service import FactService
from backend.seed import seed_database
from backend.routes.utils import success_response, error_response

facts_bp = Blueprint('facts', __name__, url_prefix='/api/facts')


@facts_bp.route('', methods=['GET'])
def list_facts():
    session = db_session()
    predicate = request.args.get('predicate')
    search = request.args.get('search')
    inferred = request.args.get('inferred')
    source = request.args.get('source')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 50))

    is_inferred_val = None
    if inferred is not None:
        if inferred.lower() in ('true', '1'):
            is_inferred_val = True
        elif inferred.lower() in ('false', '0'):
            is_inferred_val = False

    result = FactService.get_facts(
        session=session,
        predicate=predicate,
        search=search,
        is_inferred=is_inferred_val,
        source=source,
        page=page,
        page_size=page_size
    )
    return success_response(result)


@facts_bp.route('', methods=['POST'])
def create_fact():
    session = db_session()
    data = request.get_json() or {}

    predicate = data.get('predicate', '').strip()
    arg1 = data.get('arg1', '').strip()
    arg2 = data.get('arg2')

    if not predicate or not arg1:
        return error_response("Missing required fields: predicate, arg1", status_code=400)

    try:
        fact = FactService.create_fact(
            session=session,
            predicate=predicate,
            arg1=arg1,
            arg2=arg2,
            source="manual"
        )
        session.commit()
        return success_response(fact.to_dict(), message="Fact created successfully", status_code=201)
    except ValueError as e:
        session.rollback()
        return error_response(str(e), code="VALIDATION_ERROR", status_code=400)


@facts_bp.route('/<int:fact_id>', methods=['PUT'])
def update_fact(fact_id: int):
    session = db_session()
    data = request.get_json() or {}

    predicate = data.get('predicate', '').strip()
    arg1 = data.get('arg1', '').strip()
    arg2 = data.get('arg2')

    if not predicate or not arg1:
        return error_response("Missing required fields: predicate, arg1", status_code=400)

    try:
        fact = FactService.update_fact(
            session=session,
            fact_id=fact_id,
            predicate=predicate,
            arg1=arg1,
            arg2=arg2
        )
        session.commit()
        return success_response(fact.to_dict(), message="Fact updated successfully")
    except ValueError as e:
        session.rollback()
        return error_response(str(e), status_code=400)


@facts_bp.route('/<int:fact_id>', methods=['DELETE'])
def delete_fact(fact_id: int):
    session = db_session()
    try:
        FactService.delete_fact(session, fact_id)
        session.commit()
        return success_response({"deleted_id": fact_id}, message="Fact deleted successfully")
    except ValueError as e:
        session.rollback()
        return error_response(str(e), status_code=404)


@facts_bp.route('/import', methods=['POST'])
def import_facts():
    session = db_session()
    data = request.get_json() or {}

    action = data.get('action')
    if action == "seed":
        try:
            seed_database(session=session, force_reset=True)
            return success_response({}, message="Sample college data and rules loaded successfully")
        except Exception as e:
            session.rollback()
            return error_response(f"Failed to load sample data: {str(e)}", status_code=500)

    facts_list = data.get('facts', [])
    if not isinstance(facts_list, list):
        return error_response("Expected 'facts' list in request body", status_code=400)

    result = FactService.import_facts(session, facts_list)
    session.commit()
    return success_response(result, message=f"Imported {result['imported']} facts, skipped {result['skipped']}")


@facts_bp.route('/export', methods=['GET'])
def export_facts():
    session = db_session()
    fmt = request.args.get('format', 'json').lower()

    if fmt == 'csv':
        csv_data = FactService.export_facts_csv(session)
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=facts.csv"}
        )
    else:
        json_data = FactService.export_facts_json(session)
        return success_response(json_data)
