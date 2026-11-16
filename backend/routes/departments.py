from flask import Blueprint, request
from sqlalchemy import or_
from backend.database import db_session
from backend.models import Department, Professor, Student, Course, Fact
from backend.services.sync_service import SyncService
from backend.routes.utils import success_response, error_response

departments_bp = Blueprint('departments', __name__, url_prefix='/api/departments')


@departments_bp.route('', methods=['GET'])
def list_departments():
    session = db_session()
    departments = session.query(Department).order_by(Department.code).all()
    return success_response([d.to_dict() for d in departments])


@departments_bp.route('/<int:dept_id>', methods=['GET'])
def get_department(dept_id: int):
    session = db_session()
    dept = session.get(Department, dept_id)
    if not dept:
        return error_response(f"Department with ID {dept_id} not found", code="NOT_FOUND", status_code=404)

    facts = session.query(Fact).filter(
        or_(Fact.arg1 == dept.code, Fact.arg2 == dept.code)
    ).all()

    data = dept.to_dict()
    data["professors"] = [p.to_dict() for p in dept.professors]
    data["students"] = [s.to_dict() for s in dept.students]
    data["courses"] = [c.to_dict() for c in dept.courses]
    data["related_facts"] = [f.to_dict() for f in facts]
    return success_response(data)


@departments_bp.route('', methods=['POST'])
def create_department():
    session = db_session()
    data = request.get_json() or {}

    code = data.get('code', '').strip().upper()
    name = data.get('name', '').strip()
    head_professor_id = data.get('head_professor_id')

    if not code or not name:
        return error_response("Missing required fields: code, name", status_code=400)

    if session.query(Department).filter(or_(Department.code == code, Department.name == name)).first():
        return error_response("Department code or name already exists", code="DUPLICATE", status_code=409)

    head_prof = None
    if head_professor_id:
        head_prof = session.get(Professor, head_professor_id)
        if not head_prof:
            return error_response("Head professor not found", code="NOT_FOUND", status_code=404)

    dept = Department(code=code, name=name, head_professor_id=head_prof.id if head_prof else None)
    session.add(dept)
    session.flush()

    SyncService.sync_department_created(session, dept)
    if head_prof:
        SyncService.sync_department_head(session, dept.code, head_prof.name)

    session.commit()
    return success_response(dept.to_dict(), message="Department created successfully", status_code=201)


@departments_bp.route('/<int:dept_id>', methods=['PUT'])
def update_department(dept_id: int):
    session = db_session()
    dept = session.get(Department, dept_id)
    if not dept:
        return error_response(f"Department with ID {dept_id} not found", code="NOT_FOUND", status_code=404)

    data = request.get_json() or {}
    old_code = dept.code

    if 'name' in data and data['name'].strip():
        dept.name = data['name'].strip()

    if 'code' in data and data['code'].strip():
        new_code = data['code'].strip().upper()
        if new_code != old_code:
            dup = session.query(Department).filter(Department.code == new_code, Department.id != dept_id).first()
            if dup:
                return error_response("Department code already in use", code="DUPLICATE", status_code=409)
            dept.code = new_code

    if 'head_professor_id' in data:
        head_id = data['head_professor_id']
        if head_id:
            head_prof = session.query(Professor).get(head_id)
            if not head_prof:
                return error_response("Head professor not found", status_code=404)
            dept.head_professor_id = head_prof.id
            SyncService.sync_department_head(session, dept.code, head_prof.name)
        else:
            dept.head_professor_id = None
            SyncService.sync_department_head(session, dept.code, None)

    session.flush()

    if dept.code != old_code:
        SyncService.remove_facts_mentioning(session, old_code)
        SyncService.sync_department_created(session, dept)
        if dept.head_professor:
            SyncService.sync_department_head(session, dept.code, dept.head_professor.name)

    session.commit()
    return success_response(dept.to_dict(), message="Department updated successfully")


@departments_bp.route('/<int:dept_id>', methods=['DELETE'])
def delete_department(dept_id: int):
    session = db_session()
    dept = session.get(Department, dept_id)
    if not dept:
        return error_response(f"Department with ID {dept_id} not found", code="NOT_FOUND", status_code=404)

    code = dept.code
    session.delete(dept)
    SyncService.sync_department_deleted(session, code)
    session.commit()
    return success_response({"deleted_id": dept_id, "code": code}, message="Department deleted successfully")


@departments_bp.route('/<int:dept_id>/set-head', methods=['POST'])
def set_department_head(dept_id: int):
    session = db_session()
    dept = session.get(Department, dept_id)
    if not dept:
        return error_response(f"Department with ID {dept_id} not found", code="NOT_FOUND", status_code=404)

    data = request.get_json() or {}
    prof_id = data.get('professor_id')
    prof_name = data.get('professor_name')

    prof = None
    if prof_id:
        prof = session.get(Professor, prof_id)
    elif prof_name:
        prof = session.query(Professor).filter(Professor.name == prof_name.strip()).first()

    if not prof:
        return error_response("Professor not found", code="NOT_FOUND", status_code=404)

    dept.head_professor_id = prof.id
    session.flush()

    SyncService.sync_department_head(session, dept.code, prof.name)
    session.commit()

    return success_response(dept.to_dict(), message=f"Set {prof.name} as head of {dept.code}")
