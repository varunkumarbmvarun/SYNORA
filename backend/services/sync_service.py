from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from backend.models import Fact, ActivityLog, Department, Professor, Student, Course


class SyncService:
    @staticmethod
    def log_activity(session: Session, action: str, entity: str, detail: str) -> ActivityLog:
        log = ActivityLog(action=action, entity=entity, detail=detail)
        session.add(log)
        return log

    @staticmethod
    def get_or_create_fact(
        session: Session,
        predicate: str,
        arg1: str,
        arg2: Optional[str] = None,
        source: str = "entity_sync",
        is_inferred: bool = False,
        source_rule_id: Optional[int] = None
    ) -> Fact:
        # Standardize empty string or None for arg2
        norm_arg2 = arg2 if arg2 else None

        q = session.query(Fact).filter(
            Fact.predicate == predicate,
            Fact.arg1 == arg1
        )
        if norm_arg2 is not None:
            q = q.filter(Fact.arg2 == norm_arg2)
        else:
            q = q.filter(Fact.arg2.is_(None))

        fact = q.first()
        if not fact:
            fact = Fact(
                predicate=predicate,
                arg1=arg1,
                arg2=norm_arg2,
                source=source,
                is_inferred=is_inferred,
                source_rule_id=source_rule_id
            )
            session.add(fact)
            session.flush()
        return fact

    @staticmethod
    def remove_fact(
        session: Session,
        predicate: str,
        arg1: str,
        arg2: Optional[str] = None
    ):
        norm_arg2 = arg2 if arg2 else None
        q = session.query(Fact).filter(
            Fact.predicate == predicate,
            Fact.arg1 == arg1
        )
        if norm_arg2 is not None:
            q = q.filter(Fact.arg2 == norm_arg2)
        else:
            q = q.filter(Fact.arg2.is_(None))
        q.delete(synchronize_session=False)

    @staticmethod
    def remove_facts_mentioning(session: Session, constant: str):
        """Remove base and inferred facts mentioning an entity, and clean up derived facts."""
        session.query(Fact).filter(
            or_(Fact.arg1 == constant, Fact.arg2 == constant)
        ).delete(synchronize_session=False)

    # ---------------- Department Sync ----------------
    @classmethod
    def sync_department_created(cls, session: Session, dept: Department):
        cls.get_or_create_fact(session, "Department", dept.code)
        cls.log_activity(session, "CREATE", "Department", f"Department {dept.code} ({dept.name}) created")

    @classmethod
    def sync_department_deleted(cls, session: Session, dept_code: str):
        cls.remove_facts_mentioning(session, dept_code)
        cls.log_activity(session, "DELETE", "Department", f"Department {dept_code} and associated facts deleted")

    @classmethod
    def sync_department_head(
        cls,
        session: Session,
        dept_code: str,
        new_prof_name: Optional[str],
        old_prof_name: Optional[str] = None
    ):
        # Remove previous head facts for this dept
        session.query(Fact).filter(
            Fact.predicate == "HeadOf",
            Fact.arg2 == dept_code
        ).delete(synchronize_session=False)

        if new_prof_name:
            cls.get_or_create_fact(session, "HeadOf", new_prof_name, dept_code)
            cls.log_activity(session, "UPDATE", "Department", f"Set {new_prof_name} as head of {dept_code}")

    # ---------------- Professor Sync ----------------
    @classmethod
    def sync_professor_created(cls, session: Session, prof: Professor, dept_code: str):
        cls.get_or_create_fact(session, "Professor", prof.name)
        cls.get_or_create_fact(session, "BelongsTo", prof.name, dept_code)
        cls.log_activity(session, "CREATE", "Professor", f"Professor {prof.name} added to {dept_code}")

    @classmethod
    def sync_professor_deleted(cls, session: Session, prof_name: str):
        cls.remove_facts_mentioning(session, prof_name)
        cls.log_activity(session, "DELETE", "Professor", f"Professor {prof_name} and related facts removed")

    # ---------------- Student Sync ----------------
    @classmethod
    def sync_student_created(cls, session: Session, student: Student, dept_code: str):
        cls.get_or_create_fact(session, "Student", student.name)
        cls.get_or_create_fact(session, "BelongsTo", student.name, dept_code)
        cls.log_activity(session, "CREATE", "Student", f"Student {student.name} enrolled in {dept_code}")

    @classmethod
    def sync_student_deleted(cls, session: Session, student_name: str):
        cls.remove_facts_mentioning(session, student_name)
        cls.log_activity(session, "DELETE", "Student", f"Student {student_name} and related facts removed")

    # ---------------- Course Sync ----------------
    @classmethod
    def sync_course_created(cls, session: Session, course: Course, dept_code: str):
        cls.get_or_create_fact(session, "Course", course.alias)
        cls.get_or_create_fact(session, "OfferedBy", course.alias, dept_code)
        cls.log_activity(session, "CREATE", "Course", f"Course {course.name} ({course.alias}) added")

    @classmethod
    def sync_course_deleted(cls, session: Session, course_alias: str):
        cls.remove_facts_mentioning(session, course_alias)
        cls.log_activity(session, "DELETE", "Course", f"Course {course_alias} and related facts removed")

    # ---------------- Relationships Sync ----------------
    @classmethod
    def sync_enrollment(cls, session: Session, student_name: str, course_alias: str, action: str = "add"):
        if action == "add":
            cls.get_or_create_fact(session, "Enrolled", student_name, course_alias)
            cls.log_activity(session, "ENROLL", "Student", f"{student_name} enrolled in {course_alias}")
        else:
            cls.remove_fact(session, "Enrolled", student_name, course_alias)
            cls.log_activity(session, "UNENROLL", "Student", f"{student_name} un-enrolled from {course_alias}")

    @classmethod
    def sync_teaching(cls, session: Session, prof_name: str, course_alias: str, action: str = "add"):
        if action == "add":
            cls.get_or_create_fact(session, "Teaches", prof_name, course_alias)
            cls.log_activity(session, "ASSIGN", "Professor", f"{prof_name} assigned to teach {course_alias}")
        else:
            cls.remove_fact(session, "Teaches", prof_name, course_alias)
            cls.log_activity(session, "UNASSIGN", "Professor", f"{prof_name} unassigned from {course_alias}")

    @classmethod
    def sync_prerequisite(cls, session: Session, prereq_alias: str, target_alias: str, action: str = "add"):
        if action == "add":
            cls.get_or_create_fact(session, "Prerequisite", prereq_alias, target_alias)
            cls.log_activity(session, "PREREQUISITE", "Course", f"{prereq_alias} set as prerequisite for {target_alias}")
        else:
            cls.remove_fact(session, "Prerequisite", prereq_alias, target_alias)
            cls.log_activity(session, "PREREQUISITE", "Course", f"{prereq_alias} removed as prerequisite for {target_alias}")
