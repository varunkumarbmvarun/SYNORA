from flask import Blueprint, request
from sqlalchemy import or_
from backend.database import db_session
from backend.models import Student, Department, Course, Fact
from backend.services.sync_service import SyncService
from backend.routes.utils import success_response, error_response

students_bp = Blueprint('students', __name__, url_prefix='/api/students')


@students_bp.route('', methods=['GET'])
def list_students():
    session = db_session()
    search = request.args.get('search', '').strip()
    dept = request.args.get('department', '').strip()

    q = session.query(Student)
    if search:
        term = f"%{search}%"
        q = q.filter(or_(Student.name.ilike(term), Student.student_code.ilike(term), Student.email.ilike(term)))
    if dept:
        q = q.join(Student.department).filter(or_(Department.code == dept.upper(), Department.name.ilike(f"%{dept}%")))

    students = q.order_by(Student.name).all()
    return success_response([s.to_dict() for s in students])


@students_bp.route('/<int:student_id>', methods=['GET'])
def get_student(student_id: int):
    session = db_session()
    student = session.get(Student, student_id)
    if not student:
        return error_response(f"Student with ID {student_id} not found", code="NOT_FOUND", status_code=404)

    # Get related facts
    facts = session.query(Fact).filter(
        or_(Fact.arg1 == student.name, Fact.arg2 == student.name)
    ).all()

    data = student.to_dict()
    data["related_facts"] = [f.to_dict() for f in facts]
    return success_response(data)


@students_bp.route('', methods=['POST'])
def create_student():
    session = db_session()
    data = request.get_json() or {}

    name = data.get('name', '').strip()
    student_code = data.get('student_code', '').strip()
    email = data.get('email', '').strip()
    semester = data.get('semester')
    department_id = data.get('department_id')
    status = data.get('status', 'Active')

    if not name or not student_code or not email or semester is None or not department_id:
        return error_response("Missing required fields: name, student_code, email, semester, department_id", status_code=400)

    try:
        semester = int(semester)
        if not (1 <= semester <= 8):
            return error_response("Semester must be between 1 and 8", status_code=400)
    except ValueError:
        return error_response("Semester must be an integer", status_code=400)

    dept = session.get(Department, department_id)
    if not dept:
        return error_response(f"Department ID {department_id} not found", code="NOT_FOUND", status_code=404)

    # Check unique
    if session.query(Student).filter(or_(Student.student_code == student_code, Student.name == name, Student.email == email)).first():
        return error_response("Student code, name, or email already exists", code="DUPLICATE", status_code=409)

    student = Student(
        student_code=student_code,
        name=name,
        email=email,
        semester=semester,
        status=status,
        department_id=dept.id
    )
    session.add(student)
    session.flush()

    # Sync FOL facts
    SyncService.sync_student_created(session, student, dept.code)
    session.commit()

    return success_response(student.to_dict(), message="Student created successfully", status_code=201)


@students_bp.route('/<int:student_id>', methods=['PUT'])
def update_student(student_id: int):
    session = db_session()
    student = session.get(Student, student_id)
    if not student:
        return error_response(f"Student with ID {student_id} not found", code="NOT_FOUND", status_code=404)

    data = request.get_json() or {}
    old_name = student.name
    old_dept_code = student.department.code

    if 'name' in data and data['name'].strip():
        new_name = data['name'].strip()
        if new_name != old_name:
            dup = session.query(Student).filter(Student.name == new_name, Student.id != student_id).first()
            if dup:
                return error_response("Student name already in use", code="DUPLICATE", status_code=409)
            student.name = new_name

    if 'student_code' in data and data['student_code'].strip():
        student.student_code = data['student_code'].strip()

    if 'email' in data and data['email'].strip():
        student.email = data['email'].strip()

    if 'semester' in data:
        student.semester = int(data['semester'])

    if 'status' in data:
        student.status = data['status']

    if 'department_id' in data:
        dept = session.query(Department).get(data['department_id'])
        if not dept:
            return error_response("Department not found", code="NOT_FOUND", status_code=404)
        student.department_id = dept.id

    session.flush()

    # If name or department changed, update facts
    if student.name != old_name or student.department.code != old_dept_code:
        SyncService.remove_facts_mentioning(session, old_name)
        SyncService.sync_student_created(session, student, student.department.code)
        for c in student.courses:
            SyncService.sync_enrollment(session, student.name, c.alias, "add")

    session.commit()
    return success_response(student.to_dict(), message="Student updated successfully")


@students_bp.route('/<int:student_id>', methods=['DELETE'])
def delete_student(student_id: int):
    session = db_session()
    student = session.get(Student, student_id)
    if not student:
        return error_response(f"Student with ID {student_id} not found", code="NOT_FOUND", status_code=404)

    student_name = student.name
    session.delete(student)
    SyncService.sync_student_deleted(session, student_name)
    session.commit()
    return success_response({"deleted_id": student_id, "name": student_name}, message="Student deleted successfully")


@students_bp.route('/<int:student_id>/enroll', methods=['POST'])
def enroll_student(student_id: int):
    session = db_session()
    student = session.get(Student, student_id)
    if not student:
        return error_response("Student not found", status_code=404)

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

    if course in student.courses:
        return error_response(f"Student is already enrolled in {course.alias}", code="DUPLICATE", status_code=409)

    student.courses.append(course)
    SyncService.sync_enrollment(session, student.name, course.alias, "add")
    session.commit()

    return success_response(student.to_dict(), message=f"Enrolled {student.name} in {course.alias}")


@students_bp.route('/<int:student_id>/unenroll', methods=['POST'])
def unenroll_student(student_id: int):
    session = db_session()
    student = session.get(Student, student_id)
    if not student:
        return error_response("Student not found", status_code=404)

    data = request.get_json() or {}
    course_id = data.get('course_id')
    course_alias = data.get('course_alias')

    course = None
    if course_id:
        course = session.query(Course).get(course_id)
    elif course_alias:
        course = session.query(Course).filter(Course.alias == course_alias.strip()).first()

    if not course or course not in student.courses:
        return error_response("Student is not enrolled in this course", status_code=400)

    student.courses.remove(course)
    SyncService.sync_enrollment(session, student.name, course.alias, "remove")
    session.commit()

    return success_response(student.to_dict(), message=f"Unenrolled {student.name} from {course.alias}")
