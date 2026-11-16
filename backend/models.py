from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime,
    ForeignKey, Table, UniqueConstraint, CheckConstraint, JSON
)
from sqlalchemy.orm import relationship
from backend.database import Base

def utc_now():
    return datetime.now(timezone.utc)

# Association Tables
enrollments = Table(
    'enrollments',
    Base.metadata,
    Column('student_id', Integer, ForeignKey('students.id', ondelete='CASCADE'), primary_key=True),
    Column('course_id', Integer, ForeignKey('courses.id', ondelete='CASCADE'), primary_key=True)
)

teaching = Table(
    'teaching',
    Base.metadata,
    Column('professor_id', Integer, ForeignKey('professors.id', ondelete='CASCADE'), primary_key=True),
    Column('course_id', Integer, ForeignKey('courses.id', ondelete='CASCADE'), primary_key=True)
)

course_prerequisites = Table(
    'course_prerequisites',
    Base.metadata,
    Column('course_id', Integer, ForeignKey('courses.id', ondelete='CASCADE'), primary_key=True),
    Column('prerequisite_id', Integer, ForeignKey('courses.id', ondelete='CASCADE'), primary_key=True),
    CheckConstraint('course_id != prerequisite_id', name='chk_no_self_prereq')
)


class Department(Base):
    __tablename__ = 'departments'

    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(120), unique=True, nullable=False)
    head_professor_id = Column(Integer, ForeignKey('professors.id', ondelete='SET NULL'), nullable=True)

    head_professor = relationship('Professor', foreign_keys=[head_professor_id], post_update=True)
    professors = relationship('Professor', back_populates='department', foreign_keys='Professor.department_id')
    students = relationship('Student', back_populates='department', cascade='all, delete-orphan')
    courses = relationship('Course', back_populates='department', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "head_professor_id": self.head_professor_id,
            "head_professor_name": self.head_professor.name if self.head_professor else None,
            "professors_count": len(self.professors) if self.professors else 0,
            "students_count": len(self.students) if self.students else 0,
            "courses_count": len(self.courses) if self.courses else 0,
        }


class Professor(Base):
    __tablename__ = 'professors'

    id = Column(Integer, primary_key=True)
    prof_code = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False)
    specialization = Column(String(150), nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)

    department = relationship('Department', back_populates='professors', foreign_keys=[department_id])
    courses = relationship('Course', secondary=teaching, back_populates='professors')

    def to_dict(self):
        return {
            "id": self.id,
            "prof_code": self.prof_code,
            "name": self.name,
            "email": self.email,
            "specialization": self.specialization,
            "department_id": self.department_id,
            "department_code": self.department.code if self.department else None,
            "department_name": self.department.name if self.department else None,
            "courses": [c.alias or c.name for c in self.courses] if self.courses else []
        }


class Student(Base):
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True)
    student_code = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False)
    semester = Column(Integer, nullable=False)
    status = Column(String(20), default="Active", nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)

    department = relationship('Department', back_populates='students')
    courses = relationship('Course', secondary=enrollments, back_populates='students')

    def to_dict(self):
        return {
            "id": self.id,
            "student_code": self.student_code,
            "name": self.name,
            "email": self.email,
            "semester": self.semester,
            "status": self.status,
            "department_id": self.department_id,
            "department_code": self.department.code if self.department else None,
            "department_name": self.department.name if self.department else None,
            "courses": [c.alias or c.name for c in self.courses] if self.courses else []
        }


class Course(Base):
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True)
    course_code = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(120), unique=True, nullable=False)
    alias = Column(String(30), unique=True, nullable=False, index=True)
    credits = Column(Integer, nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)

    department = relationship('Department', back_populates='courses')
    professors = relationship('Professor', secondary=teaching, back_populates='courses')
    students = relationship('Student', secondary=enrollments, back_populates='courses')

    # Prerequisites relationship
    # If DSA is a prerequisite of AI:
    # Course(AI).prerequisites contains Course(DSA)
    prerequisites = relationship(
        'Course',
        secondary=course_prerequisites,
        primaryjoin=(id == course_prerequisites.c.course_id),
        secondaryjoin=(id == course_prerequisites.c.prerequisite_id),
        backref='prerequisite_for'
    )

    def to_dict(self):
        return {
            "id": self.id,
            "course_code": self.course_code,
            "name": self.name,
            "alias": self.alias,
            "credits": self.credits,
            "department_id": self.department_id,
            "department_code": self.department.code if self.department else None,
            "department_name": self.department.name if self.department else None,
            "professors": [p.name for p in self.professors] if self.professors else [],
            "students_count": len(self.students) if self.students else 0,
            "students": [s.name for s in self.students] if self.students else [],
            "prerequisites": [p.alias for p in self.prerequisites] if self.prerequisites else []
        }


class Fact(Base):
    __tablename__ = 'facts'

    id = Column(Integer, primary_key=True)
    predicate = Column(String(50), nullable=False, index=True)
    arg1 = Column(String(100), nullable=False, index=True)
    arg2 = Column(String(100), nullable=True, index=True)
    is_inferred = Column(Boolean, default=False, nullable=False)
    source = Column(String(30), default="manual", nullable=False)  # manual, entity_sync, import, inference
    source_rule_id = Column(Integer, ForeignKey('rules.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint('predicate', 'arg1', 'arg2', name='uq_fact_predicate_arg1_arg2'),
    )

    def to_fol(self) -> str:
        if self.arg2:
            return f"{self.predicate}({self.arg1}, {self.arg2})"
        return f"{self.predicate}({self.arg1})"

    def to_dict(self):
        return {
            "id": self.id,
            "predicate": self.predicate,
            "arg1": self.arg1,
            "arg2": self.arg2,
            "fol": self.to_fol(),
            "is_inferred": self.is_inferred,
            "source": self.source,
            "source_rule_id": self.source_rule_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Rule(Base):
    __tablename__ = 'rules'

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    rule_text = Column(Text, nullable=False)
    is_custom = Column(Boolean, default=True, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "rule_text": self.rule_text,
            "is_custom": self.is_custom,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class InferenceResult(Base):
    __tablename__ = 'inference_results'

    id = Column(Integer, primary_key=True)
    run_type = Column(String(20), nullable=False)  # forward, backward
    goal = Column(String(200), nullable=True)
    iterations = Column(Integer, default=0, nullable=False)
    new_facts_count = Column(Integer, default=0, nullable=False)
    rules_applied = Column(JSON, default=list, nullable=False)
    steps = Column(JSON, default=list, nullable=False)
    execution_ms = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "run_type": self.run_type,
            "goal": self.goal,
            "iterations": self.iterations,
            "new_facts_count": self.new_facts_count,
            "rules_applied": self.rules_applied or [],
            "steps": self.steps or [],
            "execution_ms": self.execution_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class QueryHistory(Base):
    __tablename__ = 'query_history'

    id = Column(Integer, primary_key=True)
    question = Column(String(300), nullable=False)
    logical_query = Column(String(200), nullable=False)
    answer = Column(Text, nullable=False)
    truth_value = Column(String(20), nullable=False)  # TRUE, FALSE, UNKNOWN
    matching_facts = Column(JSON, default=list, nullable=False)
    rules_applied = Column(JSON, default=list, nullable=False)
    trace = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "question": self.question,
            "logical_query": self.logical_query,
            "answer": self.answer,
            "truth_value": self.truth_value,
            "matching_facts": self.matching_facts or [],
            "rules_applied": self.rules_applied or [],
            "trace": self.trace or {},
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ActivityLog(Base):
    __tablename__ = 'activity_log'

    id = Column(Integer, primary_key=True)
    action = Column(String(50), nullable=False)
    entity = Column(String(50), nullable=False)
    detail = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "action": self.action,
            "entity": self.entity,
            "detail": self.detail,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
