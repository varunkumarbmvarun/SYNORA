from sqlalchemy.orm import Session
from backend.models import Department, Professor, Student, Course, Fact, Rule
from backend.database import db_session, init_db
from backend.services.sync_service import SyncService

PREDEFINED_RULES = [
    (1, "Enrolled implies Studies", "∀x ∀y (Enrolled(x,y) → Studies(x,y))"),
    (2, "Professor implies Faculty", "∀x (Professor(x) → Faculty(x))"),
    (3, "Teaches implies Professor", "∀x ∀y (Teaches(x,y) → Professor(x))"),
    (4, "Teaches implies Course", "∀x ∀y (Teaches(x,y) → Course(y))"),
    (5, "BelongsTo implies Department", "∀x ∀y (BelongsTo(x,y) → Department(y))"),
    (6, "OfferedBy implies Course", "∀x ∀y (OfferedBy(x,y) → Course(x))"),
    (7, "OfferedBy implies Department", "∀x ∀y (OfferedBy(x,y) → Department(y))"),
    (8, "HeadOf implies Professor", "∀x ∀y (HeadOf(x,y) → Professor(x))"),
    (9, "HeadOf implies Department", "∀x ∀y (HeadOf(x,y) → Department(y))"),
    (10, "Prerequisite implies Course (x)", "∀x ∀y (Prerequisite(x,y) → Course(x))"),
    (11, "Enrolled implies Student", "∀x ∀y (Enrolled(x,y) → Student(x))"),
    (12, "Enrolled and OfferedBy implies AssociatedWith", "∀x ∀y ∀z (Enrolled(x,y) ∧ OfferedBy(y,z) → AssociatedWith(x,z))"),
    (13, "BelongsTo implies AssociatedWith", "∀x ∀y (BelongsTo(x,y) → AssociatedWith(x,y))"),
    (14, "HeadOf implies BelongsTo", "∀x ∀y (HeadOf(x,y) → BelongsTo(x,y))"),
    (15, "Prerequisite implies Course (y)", "∀x ∀y (Prerequisite(x,y) → Course(y))"),
]


def seed_database(session: Session = None, force_reset: bool = False):
    """Idempotent seeder for initial college knowledge base entities and rules."""
    owns_session = False
    if session is None:
        init_db()
        session = db_session()
        owns_session = True

    try:
        # Check if already seeded
        dept_count = session.query(Department).count()
        if dept_count > 0 and not force_reset:
            print("Database already contains data, skipping seed.")
            return

        if force_reset:
            # Clear all tables in dependency order
            session.query(Fact).delete()
            session.query(Rule).delete()
            session.query(Student).delete()
            session.query(Professor).delete()
            session.query(Course).delete()
            session.query(Department).delete()
            session.commit()

        print("Seeding initial College Knowledge Base data...")

        # 1. Departments (CSE, ISE / IS, ECE)
        cse = Department(code="CSE", name="Computer Science and Engineering")
        ise = Department(code="ISE", name="Information Science and Engineering")
        ece = Department(code="ECE", name="Electronics and Communication Engineering")
        session.add_all([cse, ise, ece])
        session.flush()

        SyncService.sync_department_created(session, cse)
        SyncService.sync_department_created(session, ise)
        SyncService.sync_department_created(session, ece)

        # 2. Professors (1 in each department)
        meena = Professor(
            prof_code="PROF01",
            name="Meena",
            email="meena@college.edu",
            specialization="Artificial Intelligence",
            department_id=cse.id
        )
        anand = Professor(
            prof_code="PROF02",
            name="Anand",
            email="anand@college.edu",
            specialization="Database Systems",
            department_id=ise.id
        )
        kiran = Professor(
            prof_code="PROF03",
            name="Kiran",
            email="kiran@college.edu",
            specialization="Internet of Things & Networks",
            department_id=ece.id
        )
        session.add_all([meena, anand, kiran])
        session.flush()

        SyncService.sync_professor_created(session, meena, cse.code)
        SyncService.sync_professor_created(session, anand, ise.code)
        SyncService.sync_professor_created(session, kiran, ece.code)

        # Meena heads CSE, Anand heads ISE, Kiran heads ECE
        cse.head_professor_id = meena.id
        ise.head_professor_id = anand.id
        ece.head_professor_id = kiran.id
        session.flush()

        SyncService.sync_department_head(session, cse.code, meena.name)
        SyncService.sync_department_head(session, ise.code, anand.name)
        SyncService.sync_department_head(session, ece.code, kiran.name)

        # 3. Students
        varun = Student(student_code="USN00", name="Varun", email="varun@college.edu", semester=5, status="Active", department_id=cse.id)
        ravi = Student(student_code="USN01", name="Ravi", email="ravi@college.edu", semester=5, status="Active", department_id=cse.id)
        rahul = Student(student_code="USN02", name="Rahul", email="rahul@college.edu", semester=5, status="Active", department_id=ise.id)
        priya = Student(student_code="USN03", name="Priya", email="priya@college.edu", semester=6, status="Active", department_id=ece.id)
        session.add_all([varun, ravi, rahul, priya])
        session.flush()

        SyncService.sync_student_created(session, varun, cse.code)
        SyncService.sync_student_created(session, ravi, cse.code)
        SyncService.sync_student_created(session, rahul, ise.code)
        SyncService.sync_student_created(session, priya, ece.code)

        # 4. Courses (1 offered by each department)
        ai = Course(course_code="CS501", name="Artificial Intelligence", alias="AI", credits=4, department_id=cse.id)
        dbms = Course(course_code="IS401", name="Database Management Systems", alias="DBMS", credits=4, department_id=ise.id)
        iot = Course(course_code="EC501", name="Internet of Things", alias="IOT", credits=4, department_id=ece.id)
        session.add_all([ai, dbms, iot])
        session.flush()

        SyncService.sync_course_created(session, ai, cse.code)
        SyncService.sync_course_created(session, dbms, ise.code)
        SyncService.sync_course_created(session, iot, ece.code)

        # 5. Enrollments
        # AI is a cross-departmental core/elective taken by Varun (CSE), Ravi (CSE), Rahul (ISE), and Priya (ECE)
        # Rahul also studies DBMS (ISE), and Priya also studies IOT (ECE)
        varun.courses.append(ai)
        ravi.courses.append(ai)
        rahul.courses.extend([ai, dbms])
        priya.courses.extend([ai, iot])
        session.flush()

        SyncService.sync_enrollment(session, "Varun", "AI")
        SyncService.sync_enrollment(session, "Ravi", "AI")
        SyncService.sync_enrollment(session, "Rahul", "AI")
        SyncService.sync_enrollment(session, "Rahul", "DBMS")
        SyncService.sync_enrollment(session, "Priya", "AI")
        SyncService.sync_enrollment(session, "Priya", "IOT")

        # 6. Teaching (Each professor teaches their department's course)
        meena.courses.append(ai)
        anand.courses.append(dbms)
        kiran.courses.append(iot)
        session.flush()

        SyncService.sync_teaching(session, "Meena", "AI")
        SyncService.sync_teaching(session, "Anand", "DBMS")
        SyncService.sync_teaching(session, "Kiran", "IOT")

        # 7. Prerequisites
        # DBMS is prerequisite of AI
        ai.prerequisites.append(dbms)
        session.flush()

        SyncService.sync_prerequisite(session, "DBMS", "AI")

        # 8. Rules (15 predefined rules)
        for rid, name, rule_text in PREDEFINED_RULES:
            existing_rule = session.query(Rule).filter(Rule.id == rid).first()
            if not existing_rule:
                r = Rule(id=rid, name=name, rule_text=rule_text, is_custom=False, enabled=True)
                session.add(r)
        session.flush()

        session.commit()
        print("Database successfully seeded with 15 rules and full college dataset!")

    except Exception as e:
        session.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        if owns_session:
            session.close()


if __name__ == "__main__":
    seed_database()
