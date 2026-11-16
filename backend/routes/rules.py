from flask import Blueprint, request
from backend.database import db_session
from backend.services.rule_service import RuleService
from backend.routes.utils import success_response, error_response

rules_bp = Blueprint('rules', __name__, url_prefix='/api/rules')


@rules_bp.route('', methods=['GET'])
def list_rules():
    session = db_session()
    rules = RuleService.get_rules(session)
    return success_response(rules)


@rules_bp.route('', methods=['POST'])
def create_rule():
    session = db_session()
    data = request.get_json() or {}

    name = data.get('name', '').strip()
    rule_text = data.get('rule_text', '').strip()
    enabled = data.get('enabled', True)

    if not name or not rule_text:
        return error_response("Missing required fields: name, rule_text", status_code=400)

    try:
        rule = RuleService.create_rule(
            session=session,
            name=name,
            rule_text=rule_text,
            is_custom=True,
            enabled=enabled
        )
        session.commit()
        return success_response(rule.to_dict(), message="Rule created successfully", status_code=201)
    except ValueError as e:
        session.rollback()
        return error_response(str(e), code="PARSE_ERROR", status_code=422)


@rules_bp.route('/<int:rule_id>', methods=['PUT'])
def update_rule(rule_id: int):
    session = db_session()
    data = request.get_json() or {}

    name = data.get('name')
    rule_text = data.get('rule_text')
    enabled = data.get('enabled')

    try:
        rule = RuleService.update_rule(
            session=session,
            rule_id=rule_id,
            name=name,
            rule_text=rule_text,
            enabled=enabled
        )
        session.commit()
        return success_response(rule.to_dict(), message="Rule updated successfully")
    except ValueError as e:
        session.rollback()
        return error_response(str(e), status_code=422)


@rules_bp.route('/<int:rule_id>', methods=['DELETE'])
def delete_rule(rule_id: int):
    session = db_session()
    try:
        RuleService.delete_rule(session, rule_id)
        session.commit()
        return success_response({"deleted_id": rule_id}, message="Rule deleted successfully")
    except ValueError as e:
        session.rollback()
        return error_response(str(e), status_code=400)


@rules_bp.route('/test', methods=['POST'])
def test_rule():
    session = db_session()
    data = request.get_json() or {}
    rule_text = data.get('rule_text', '').strip()

    if not rule_text:
        return error_response("Missing 'rule_text' in request body", status_code=400)

    try:
        result = RuleService.test_rule(session, rule_text)
        return success_response(result, message="Rule dry run executed successfully")
    except ValueError as e:
        return error_response(str(e), code="PARSE_ERROR", status_code=422)
