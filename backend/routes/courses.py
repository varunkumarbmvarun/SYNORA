from flask import Blueprint, request
from sqlalchemy import or_
from backend.database import db_session
from backend.models import Course, Department, Professor, Student, Fact
from backend.services.sync_service import SyncService
from backend.routes.utils import success_response, error_response

courses_bp = Blueprint('courses', __name__, url_prefix='/api/courses')


@courses_bp.route('', methods=['GET'])
def list_courses():
    session = db_session()
    search = request.args.get('search', '').strip()
    dept = request.args.get('department', '').strip()

    q = session.query(Course)
    if search:
        term = f"%{search}%"
        q = q.filter(or_(Course.name.ilike(term), Course.alias.ilike(term), Course.course_code.ilike(term)))
    if dept:
        q = q.join(Course.department).filter(or_(Department.code == dept.upper(), Department.name.ilike(f"%{dept}%")))

    courses = q.order_by(Course.alias).all()
    return success_response([c.to_dict() for c in courses])


@courses_bp.route('/<int:course_id>', methods=['GET'])
def get_course(course_id: int):
    session = db_session()
    course = session.get(Course, course_id)
    if not course:
        return error_response(f"Course with ID {course_id} not found", code="NOT_FOUND", status_code=404)

    facts = session.query(Fact).filter(
        or_(Fact.arg1 == course.alias, Fact.arg2 == course.alias)
    ).all()

    data = course.to_dict()
    data["related_facts"] = [f.to_dict() for f in facts]
    return success_response(data)


@courses_bp.route('', methods=['POST'])
def create_course():
    session = db_session()
    data = request.get_json() or {}

    course_code = data.get('course_code', '').strip()
    name = data.get('name', '').strip()
    alias = data.get('alias', '').strip()
    credits_val = data.get('credits')
    department_id = data.get('department_id')

    if not course_code or not name or not alias or credits_val is None or not department_id:
        return error_response("Missing required fields: course_code, name, alias, credits, department_id", status_code=400)

    try:
        credits_val = int(credits_val)
        if not (1 <= credits_val <= 6):
            return error_response("Credits must be between 1 and 6", status_code=400)
    except ValueError:
        return error_response("Credits must be an integer", status_code=400)

    dept = session.get(Department, department_id)
    if not dept:
        return error_response("Department not found", code="NOT_FOUND", status_code=404)

    if session.query(Course).filter(or_(Course.course_code == course_code, Course.name == name, Course.alias == alias)).first():
        return error_response("Course code, name, or alias already exists", code="DUPLICATE", status_code=409)

    course = Course(
        course_code=course_code,
        name=name,
        alias=alias,
        credits=credits_val,
        department_id=dept.id
    )
    session.add(course)
    session.flush()

    SyncService.sync_course_created(session, course, dept.code)
    session.commit()

    return success_response(course.to_dict(), message="Course created successfully", status_code=201)


@courses_bp.route('/<int:course_id>', methods=['PUT'])
def update_course(course_id: int):
    session = db_session()
    course = session.get(Course, course_id)
    if not course:
        return error_response(f"Course with ID {course_id} not found", code="NOT_FOUND", status_code=404)

    data = request.get_json() or {}
    old_alias = course.alias
    old_dept_code = course.department.code

    if 'name' in data and data['name'].strip():
        course.name = data['name'].strip()

    if 'alias' in data and data['alias'].strip():
        new_alias = data['alias'].strip()
        if new_alias != old_alias:
            dup = session.query(Course).filter(Course.alias == new_alias, Course.id != course_id).first()
            if dup:
                return error_response("Course alias already in use", code="DUPLICATE", status_code=409)
            course.alias = new_alias

    if 'course_code' in data and data['course_code'].strip():
        course.course_code = data['course_code'].strip()

    if 'credits' in data:
        course.credits = int(data['credits'])

    if 'department_id' in data:
        dept = session.query(Department).get(data['department_id'])
        if not dept:
            return error_response("Department not found", code="NOT_FOUND", status_code=404)
        course.department_id = dept.id

    session.flush()

    if course.alias != old_alias or course.department.code != old_dept_code:
        SyncService.remove_facts_mentioning(session, old_alias)
        SyncService.sync_course_created(session, course, course.department.code)
        for p in course.professors:
            SyncService.sync_teaching(session, p.name, course.alias, "add")
        for s in course.students:
            SyncService.sync_enrollment(session, s.name, course.alias, "add")
        for pr in course.prerequisites:
            SyncService.sync_prerequisite(session, pr.alias, course.alias, "add")

    session.commit()
    return success_response(course.to_dict(), message="Course updated successfully")


@courses_bp.route('/<int:course_id>', methods=['DELETE'])
def delete_course(course_id: int):
    session = db_session()
    course = session.get(Course, course_id)
    if not course:
        return error_response(f"Course with ID {course_id} not found", code="NOT_FOUND", status_code=404)

    alias = course.alias
    session.delete(course)
    SyncService.sync_course_deleted(session, alias)
    session.commit()
    return success_response({"deleted_id": course_id, "alias": alias}, message="Course deleted successfully")


@courses_bp.route('/<int:course_id>/prerequisites', methods=['POST'])
def add_prerequisite(course_id: int):
    session = db_session()
    course = session.get(Course, course_id)
    if not course:
        return error_response("Course not found", status_code=404)

    data = request.get_json() or {}
    prereq_id = data.get('prerequisite_id')
    prereq_alias = data.get('prerequisite_alias')

    prereq = None
    if prereq_id:
        prereq = session.get(Course, prereq_id)
    elif prereq_alias:
        prereq = session.query(Course).filter(Course.alias == prereq_alias.strip()).first()

    if not prereq:
        return error_response("Prerequisite course not found", status_code=404)

    if prereq.id == course.id:
        return error_response("A course cannot be a prerequisite of itself", status_code=400)

    if prereq in course.prerequisites:
        return error_response("Prerequisite already assigned", code="DUPLICATE", status_code=409)

    # Check for simple cycle: does course appear in prereq.prerequisites?
    if course in prereq.prerequisites:
        return error_response("Circular prerequisite dependency detected", status_code=400)

    course.prerequisites.append(prereq)
    SyncService.sync_prerequisite(session, prereq.alias, course.alias, "add")
    session.commit()

    return success_response(course.to_dict(), message=f"Added {prereq.alias} as prerequisite for {course.alias}")


@courses_bp.route('/<int:course_id>/prerequisites/<int:prereq_id>', methods=['DELETE'])
def remove_prerequisite(course_id: int, prereq_id: int):
    session = db_session()
    course = session.get(Course, course_id)
    prereq = session.get(Course, prereq_id)

    if not course or not prereq:
        return error_response("Course or prerequisite not found", status_code=404)

    if prereq not in course.prerequisites:
        return error_response("Prerequisite not linked to this course", status_code=400)

    course.prerequisites.remove(prereq)
    SyncService.sync_prerequisite(session, prereq.alias, course.alias, "remove")
    session.commit()

    return success_response(course.to_dict(), message=f"Removed {prereq.alias} as prerequisite from {course.alias}")
