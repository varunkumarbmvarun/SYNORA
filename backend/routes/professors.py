from flask import Blueprint, request
from sqlalchemy import or_
from backend.database import db_session
from backend.models import Professor, Department, Course, Fact
from backend.services.sync_service import SyncService
from backend.routes.utils import success_response, error_response

professors_bp = Blueprint('professors', __name__, url_prefix='/api/professors')


@professors_bp.route('', methods=['GET'])
def list_professors():
    session = db_session()
    search = request.args.get('search', '').strip()
    dept = request.args.get('department', '').strip()

    q = session.query(Professor)
    if search:
        term = f"%{search}%"
        q = q.filter(or_(Professor.name.ilike(term), Professor.prof_code.ilike(term), Professor.specialization.ilike(term)))
    if dept:
        q = q.join(Professor.department).filter(or_(Department.code == dept.upper(), Department.name.ilike(f"%{dept}%")))

    professors = q.order_by(Professor.name).all()
    return success_response([p.to_dict() for p in professors])


@professors_bp.route('/<int:prof_id>', methods=['GET'])
def get_professor(prof_id: int):
    session = db_session()
    prof = session.get(Professor, prof_id)
    if not prof:
        return error_response(f"Professor with ID {prof_id} not found", code="NOT_FOUND", status_code=404)

    facts = session.query(Fact).filter(
        or_(Fact.arg1 == prof.name, Fact.arg2 == prof.name)
    ).all()

    data = prof.to_dict()
    data["related_facts"] = [f.to_dict() for f in facts]
    return success_response(data)


@professors_bp.route('', methods=['POST'])
def create_professor():
    session = db_session()
    data = request.get_json() or {}

    name = data.get('name', '').strip()
    prof_code = data.get('prof_code', '').strip()
    email = data.get('email', '').strip()
    specialization = data.get('specialization', '').strip()
    department_id = data.get('department_id')

    if not name or not prof_code or not email or not specialization or not department_id:
        return error_response("Missing required fields: name, prof_code, email, specialization, department_id", status_code=400)

    dept = session.get(Department, department_id)
    if not dept:
        return error_response(f"Department ID {department_id} not found", code="NOT_FOUND", status_code=404)

    if session.query(Professor).filter(or_(Professor.prof_code == prof_code, Professor.name == name, Professor.email == email)).first():
        return error_response("Professor code, name, or email already exists", code="DUPLICATE", status_code=409)

    prof = Professor(
        prof_code=prof_code,
        name=name,
        email=email,
        specialization=specialization,
        department_id=dept.id
    )
    session.add(prof)
    session.flush()

    SyncService.sync_professor_created(session, prof, dept.code)
    session.commit()

    return success_response(prof.to_dict(), message="Professor created successfully", status_code=201)


@professors_bp.route('/<int:prof_id>', methods=['PUT'])
def update_professor(prof_id: int):
    session = db_session()
    prof = session.get(Professor, prof_id)
    if not prof:
        return error_response(f"Professor with ID {prof_id} not found", code="NOT_FOUND", status_code=404)

    data = request.get_json() or {}
    old_name = prof.name
    old_dept_code = prof.department.code

    if 'name' in data and data['name'].strip():
        new_name = data['name'].strip()
        if new_name != old_name:
            dup = session.query(Professor).filter(Professor.name == new_name, Professor.id != prof_id).first()
            if dup:
                return error_response("Professor name already in use", code="DUPLICATE", status_code=409)
            prof.name = new_name

    if 'prof_code' in data and data['prof_code'].strip():
        prof.prof_code = data['prof_code'].strip()

    if 'email' in data and data['email'].strip():
        prof.email = data['email'].strip()

    if 'specialization' in data and data['specialization'].strip():
        prof.specialization = data['specialization'].strip()

    if 'department_id' in data:
        dept = session.query(Department).get(data['department_id'])
        if not dept:
            return error_response("Department not found", code="NOT_FOUND", status_code=404)
        prof.department_id = dept.id

    session.flush()

    if prof.name != old_name or prof.department.code != old_dept_code:
        SyncService.remove_facts_mentioning(session, old_name)
        SyncService.sync_professor_created(session, prof, prof.department.code)
        for c in prof.courses:
            SyncService.sync_teaching(session, prof.name, c.alias, "add")

    session.commit()
    return success_response(prof.to_dict(), message="Professor updated successfully")


@professors_bp.route('/<int:prof_id>', methods=['DELETE'])
def delete_professor(prof_id: int):
    session = db_session()
    prof = session.get(Professor, prof_id)
    if not prof:
        return error_response(f"Professor with ID {prof_id} not found", code="NOT_FOUND", status_code=404)

    prof_name = prof.name
    session.delete(prof)
    SyncService.sync_professor_deleted(session, prof_name)
    session.commit()
    return success_response({"deleted_id": prof_id, "name": prof_name}, message="Professor deleted successfully")


@professors_bp.route('/<int:prof_id>/assign', methods=['POST'])
def assign_course(prof_id: int):
    session = db_session()
    prof = session.get(Professor, prof_id)
    if not prof:
        return error_response("Professor not found", status_code=404)

    data = request.get_json() or {}
    course_id = data.get('course_id')
    course_alias = data.get('course_alias')

    course = None
    if course_id:
        course = session.query(Course).get(course_id)
    elif course_alias:
        course = session.query(Course).filter(Course.alias == course_alias.strip()).first()

    if not course:
        return error_response("Course not found", status_code=404)

    if course in prof.courses:
        return error_response("Professor is already assigned to this course", code="DUPLICATE", status_code=409)

    prof.courses.append(course)
    SyncService.sync_teaching(session, prof.name, course.alias, "add")
    session.commit()

    return success_response(prof.to_dict(), message=f"Assigned {prof.name} to teach {course.alias}")


@professors_bp.route('/<int:prof_id>/unassign', methods=['POST'])
def unassign_course(prof_id: int):
    session = db_session()
    prof = session.get(Professor, prof_id)
    if not prof:
        return error_response("Professor not found", status_code=404)

    data = request.get_json() or {}
    course_id = data.get('course_id')
    course_alias = data.get('course_alias')

    course = None
    if course_id:
        course = session.query(Course).get(course_id)
    elif course_alias:
        course = session.query(Course).filter(Course.alias == course_alias.strip()).first()

    if not course or course not in prof.courses:
        return error_response("Professor is not assigned to this course", status_code=400)

    prof.courses.remove(course)
    SyncService.sync_teaching(session, prof.name, course.alias, "remove")
    session.commit()

    return success_response(prof.to_dict(), message=f"Unassigned {prof.name} from {course.alias}")
