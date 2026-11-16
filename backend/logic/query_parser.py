import re
from typing import List, Dict, Tuple, Optional, Any
from backend.logic.terms import Atom, Term, Constant, Variable
from backend.logic.parser import parse_atom, ATOM_PATTERN


class EntityCatalog:
    """Live entity map for extracting and normalizing constants."""
    def __init__(
        self,
        students: Optional[List[str]] = None,
        professors: Optional[List[str]] = None,
        courses: Optional[Dict[str, str]] = None,  # name/alias -> canonical alias
        departments: Optional[Dict[str, str]] = None  # name/code -> canonical code
    ):
        self.students = {s.lower(): s for s in (students or [])}
        self.professors = {p.lower(): p for p in (professors or [])}
        self.courses = {k.lower(): v for k, v in (courses or {}).items()}
        self.departments = {k.lower(): v for k, v in (departments or {}).items()}

    def resolve_student(self, text: str) -> Optional[str]:
        t = text.strip().lower()
        if t in self.students:
            return self.students[t]
        for s_lower, s_name in self.students.items():
            if re.search(rf'\b{re.escape(s_lower)}\b', t):
                return s_name
        return None

    def resolve_professor(self, text: str) -> Optional[str]:
        t = text.strip().lower()
        if t in self.professors:
            return self.professors[t]
        for p_lower, p_name in self.professors.items():
            if re.search(rf'\b{re.escape(p_lower)}\b', t):
                return p_name
        return None

    def resolve_course(self, text: str) -> Optional[str]:
        t = text.strip().lower()
        if t in self.courses:
            return self.courses[t]
        # Match longest course phrase first
        sorted_keys = sorted(self.courses.keys(), key=len, reverse=True)
        for c_key in sorted_keys:
            if re.search(rf'\b{re.escape(c_key)}\b', t):
                return self.courses[c_key]
        return None

    def resolve_department(self, text: str) -> Optional[str]:
        t = text.strip().lower()
        if t in self.departments:
            return self.departments[t]
        sorted_keys = sorted(self.departments.keys(), key=len, reverse=True)
        for d_key in sorted_keys:
            if re.search(rf'\b{re.escape(d_key)}\b', t):
                return self.departments[d_key]
        return None

    def resolve_any_entity(self, text: str) -> Optional[str]:
        t = text.strip()
        # Direct lookup or clean identifier
        return (
            self.resolve_course(t) or
            self.resolve_department(t) or
            self.resolve_professor(t) or
            self.resolve_student(t) or
            t.capitalize().replace(" ", "_")
        )


def parse_natural_language_query(
    question: str,
    catalog: Optional[EntityCatalog] = None
) -> Tuple[List[Atom], str]:
    """
    Parse a natural-language question or raw logical query into a list of Atoms.
    Returns (list_of_atoms, display_query_string).
    """
    raw = question.strip()
    if not raw:
        raise ValueError("Question cannot be empty.")

    # 1. Direct FOL syntax check: e.g. "Studies(x, AI)" or "Studies(Ravi, y) & Teaches(x, y)"
    if ATOM_PATTERN.search(raw):
        # Could be directly an FOL query!
        # Clean quantifiers or split conjunctions
        cleaned = raw.replace('∧', '&').replace('AND', '&')
        atom_strings = [m.group(0) for m in ATOM_PATTERN.finditer(cleaned)]
        if atom_strings:
            atoms = [parse_atom(s, allow_variables=True) for s in atom_strings]
            display = " ∧ ".join(str(a) for a in atoms)
            return atoms, display

    if catalog is None:
        catalog = EntityCatalog()

    q = raw.rstrip('?').strip()
    q_lower = q.lower()

    # Pattern 1: "Who is <student>'s professor?" / "Who is the professor of <student>?"
    m = re.search(r"who is ([a-zA-Z0-9_\s]+)'s professor", q_lower) or \
        re.search(r"who is (?:the )?professor of ([a-zA-Z0-9_\s]+)", q_lower) or \
        re.search(r"who teaches ([a-zA-Z0-9_\s]+)\b", q_lower)
    if m:
        candidate = m.group(1).strip()
        # Ensure it's not a course
        course = catalog.resolve_course(candidate)
        if not course:
            student = catalog.resolve_student(candidate) or candidate.capitalize()
            atoms = [
                Atom("Studies", (Constant(student), Variable("y"))),
                Atom("Teaches", (Variable("x"), Variable("y")))
            ]
            return atoms, f"Studies({student}, y) ∧ Teaches(x, y)"

    # Pattern 2: "Which professors belong to <dept>?" / "Who belongs to <dept>?"
    m = re.search(r"(?:which|what) professors belong to ([a-zA-Z0-9_\s]+)", q_lower) or \
        re.search(r"professors in ([a-zA-Z0-9_\s]+)", q_lower) or \
        re.search(r"who belongs to ([a-zA-Z0-9_\s]+)", q_lower)
    if m:
        dept = catalog.resolve_department(m.group(1)) or m.group(1).upper()
        atoms = [
            Atom("BelongsTo", (Variable("x"), Constant(dept))),
            Atom("Professor", (Variable("x"),))
        ]
        return atoms, f"BelongsTo(x, {dept}) ∧ Professor(x)"

    # Pattern 3: "Who teaches <course>?" / "Which professor teaches <course>?"
    m = re.search(r"who teaches ([a-zA-Z0-9_\s]+)", q_lower) or \
        re.search(r"which professor teaches ([a-zA-Z0-9_\s]+)", q_lower)
    if m:
        course = catalog.resolve_course(m.group(1)) or m.group(1).upper()
        atoms = [Atom("Teaches", (Variable("x"), Constant(course)))]
        return atoms, f"Teaches(x, {course})"

    # Pattern 4: "What does <prof> teach?" / "Which courses does <prof> teach?"
    m = re.search(r"what does ([a-zA-Z0-9_\s]+) teach", q_lower) or \
        re.search(r"(?:which|what) courses does ([a-zA-Z0-9_\s]+) teach", q_lower) or \
        re.search(r"courses taught by ([a-zA-Z0-9_\s]+)", q_lower)
    if m:
        prof = catalog.resolve_professor(m.group(1)) or m.group(1).capitalize()
        atoms = [Atom("Teaches", (Constant(prof), Variable("x")))]
        return atoms, f"Teaches({prof}, x)"

    # Pattern 5: "Which students are enrolled in <course>?" / "Who is enrolled in <course>?"
    m = re.search(r"(?:which|what) students are enrolled in ([a-zA-Z0-9_\s]+)", q_lower) or \
        re.search(r"who is enrolled in ([a-zA-Z0-9_\s]+)", q_lower)
    if m:
        course = catalog.resolve_course(m.group(1)) or m.group(1).upper()
        atoms = [Atom("Enrolled", (Variable("x"), Constant(course)))]
        return atoms, f"Enrolled(x, {course})"

    # Pattern 6: "Which students study <course>?" / "Who studies <course>?"
    m = re.search(r"(?:which|what) students study ([a-zA-Z0-9_\s]+)", q_lower) or \
        re.search(r"who studies ([a-zA-Z0-9_\s]+)", q_lower)
    if m:
        course = catalog.resolve_course(m.group(1)) or m.group(1).upper()
        atoms = [Atom("Studies", (Variable("x"), Constant(course)))]
        return atoms, f"Studies(x, {course})"

    # Pattern 7: "What courses is <student> studying?" / "What is <student> studying?" / "What does <student> study?"
    m = re.search(r"(?:which|what) courses is ([a-zA-Z0-9_\s]+) studying", q_lower) or \
        re.search(r"what is ([a-zA-Z0-9_\s]+) studying", q_lower) or \
        re.search(r"what does ([a-zA-Z0-9_\s]+) study", q_lower)
    if m:
        student = catalog.resolve_student(m.group(1)) or m.group(1).capitalize()
        atoms = [Atom("Studies", (Constant(student), Variable("x")))]
        return atoms, f"Studies({student}, x)"

    # Pattern 8: "What courses is <student> enrolled in?" / "What is <student> enrolled in?"
    m = re.search(r"(?:which|what) courses is ([a-zA-Z0-9_\s]+) enrolled in", q_lower) or \
        re.search(r"what is ([a-zA-Z0-9_\s]+) enrolled in", q_lower)
    if m:
        student = catalog.resolve_student(m.group(1)) or m.group(1).capitalize()
        atoms = [Atom("Enrolled", (Constant(student), Variable("x")))]
        return atoms, f"Enrolled({student}, x)"

    # Pattern 9: "Who is the head of <dept>?" / "Head of <dept>?"
    m = re.search(r"who is (?:the )?head of ([a-zA-Z0-9_\s]+)", q_lower) or \
        re.search(r"^head of ([a-zA-Z0-9_\s]+)", q_lower)
    if m:
        dept = catalog.resolve_department(m.group(1)) or m.group(1).upper()
        atoms = [Atom("HeadOf", (Variable("x"), Constant(dept)))]
        return atoms, f"HeadOf(x, {dept})"

    # Pattern 10: "Which courses are offered by <dept>?" / "What courses are offered by <dept>?"
    m = re.search(r"(?:which|what) courses are offered by ([a-zA-Z0-9_\s]+)", q_lower) or \
        re.search(r"courses offered by ([a-zA-Z0-9_\s]+)", q_lower)
    if m:
        dept = catalog.resolve_department(m.group(1)) or m.group(1).upper()
        atoms = [Atom("OfferedBy", (Variable("x"), Constant(dept)))]
        return atoms, f"OfferedBy(x, {dept})"

    # Pattern 11: "What are the prerequisites of <course>?" / "What is the prerequisite of <course>?"
    m = re.search(r"(?:what are the|what is the) prerequisites? of ([a-zA-Z0-9_\s]+)", q_lower) or \
        re.search(r"prerequisites? (?:of|for) ([a-zA-Z0-9_\s]+)", q_lower)
    if m:
        course = catalog.resolve_course(m.group(1)) or m.group(1).upper()
        atoms = [Atom("Prerequisite", (Variable("x"), Constant(course)))]
        return atoms, f"Prerequisite(x, {course})"

    # Pattern 12: "Which courses have prerequisites?" / "Courses with prerequisites"
    if "courses have prerequisites" in q_lower or "courses with prerequisites" in q_lower:
        atoms = [Atom("Prerequisite", (Variable("x"), Variable("y")))]
        return atoms, "Prerequisite(x, y)"

    # Pattern 13: "Is <person> enrolled in <course>?"
    m = re.search(r"is ([a-zA-Z0-9_\s]+) enrolled in ([a-zA-Z0-9_\s]+)", q_lower)
    if m:
        person = catalog.resolve_student(m.group(1)) or m.group(1).capitalize()
        course = catalog.resolve_course(m.group(2)) or m.group(2).upper()
        atoms = [Atom("Enrolled", (Constant(person), Constant(course)))]
        return atoms, f"Enrolled({person}, {course})"

    # Pattern 14: "Does <person> study <course>?" / "Is <person> studying <course>?"
    m = re.search(r"does ([a-zA-Z0-9_\s]+) study ([a-zA-Z0-9_\s]+)", q_lower) or \
        re.search(r"is ([a-zA-Z0-9_\s]+) studying ([a-zA-Z0-9_\s]+)", q_lower)
    if m:
        person = catalog.resolve_student(m.group(1)) or m.group(1).capitalize()
        course = catalog.resolve_course(m.group(2)) or m.group(2).upper()
        atoms = [Atom("Studies", (Constant(person), Constant(course)))]
        return atoms, f"Studies({person}, {course})"

    # Pattern 15: "Does <person> teach <course>?" / "Is <person> teaching <course>?"
    m = re.search(r"does ([a-zA-Z0-9_\s]+) teach ([a-zA-Z0-9_\s]+)", q_lower) or \
        re.search(r"is ([a-zA-Z0-9_\s]+) teaching ([a-zA-Z0-9_\s]+)", q_lower)
    if m:
        prof = catalog.resolve_professor(m.group(1)) or m.group(1).capitalize()
        course = catalog.resolve_course(m.group(2)) or m.group(2).upper()
        atoms = [Atom("Teaches", (Constant(prof), Constant(course)))]
        return atoms, f"Teaches({prof}, {course})"

    # Pattern 16: "Is <person> associated with <dept>?" / "Is <person> associated to <dept>?"
    m = re.search(r"is ([a-zA-Z0-9_\s]+) associated with ([a-zA-Z0-9_\s]+)", q_lower) or \
        re.search(r"is ([a-zA-Z0-9_\s]+) associated to ([a-zA-Z0-9_\s]+)", q_lower)
    if m:
        person = catalog.resolve_student(m.group(1)) or catalog.resolve_professor(m.group(1)) or m.group(1).capitalize()
        dept = catalog.resolve_department(m.group(2)) or m.group(2).upper()
        atoms = [Atom("AssociatedWith", (Constant(person), Constant(dept)))]
        return atoms, f"AssociatedWith({person}, {dept})"

    # Pattern 17: "Is <person> a professor?" / "Is <person> professor?"
    m = re.search(r"is ([a-zA-Z0-9_\s]+) a professor\b", q_lower) or \
        re.search(r"is ([a-zA-Z0-9_\s]+) professor\b", q_lower)
    if m:
        person = catalog.resolve_professor(m.group(1)) or m.group(1).capitalize()
        atoms = [Atom("Professor", (Constant(person),))]
        return atoms, f"Professor({person})"

    # Pattern 18: "Is <person> a student?" / "Is <person> student?"
    m = re.search(r"is ([a-zA-Z0-9_\s]+) a student\b", q_lower) or \
        re.search(r"is ([a-zA-Z0-9_\s]+) student\b", q_lower)
    if m:
        person = catalog.resolve_student(m.group(1)) or m.group(1).capitalize()
        atoms = [Atom("Student", (Constant(person),))]
        return atoms, f"Student({person})"

    # Pattern 19: "Is <person> head of <dept>?"
    m = re.search(r"is ([a-zA-Z0-9_\s]+) (?:the )?head of ([a-zA-Z0-9_\s]+)", q_lower)
    if m:
        person = catalog.resolve_professor(m.group(1)) or m.group(1).capitalize()
        dept = catalog.resolve_department(m.group(2)) or m.group(2).upper()
        atoms = [Atom("HeadOf", (Constant(person), Constant(dept)))]
        return atoms, f"HeadOf({person}, {dept})"

    # Pattern 20: "Which students are associated with <dept>?" / "Who is associated with <dept>?"
    m = re.search(r"(?:which students|who) is associated with ([a-zA-Z0-9_\s]+)", q_lower) or \
        re.search(r"(?:which students|who) are associated with ([a-zA-Z0-9_\s]+)", q_lower)
    if m:
        dept = catalog.resolve_department(m.group(1)) or m.group(1).upper()
        atoms = [Atom("AssociatedWith", (Variable("x"), Constant(dept)))]
        return atoms, f"AssociatedWith(x, {dept})"

    # Pattern 21: "Who is <person>?" / "Tell me about <person>"
    m = re.search(r"^(?:who is|tell me about)\s+([a-zA-Z0-9_\s]+)$", q_lower)
    if m:
        cand = m.group(1).strip()
        if not cand.startswith(("the head", "head of", "enrolled", "associated", "professor of", "the professor")):
            prof = catalog.resolve_professor(cand)
            if prof:
                return [Atom("Professor", (Constant(prof),))], f"Professor({prof})"
            student = catalog.resolve_student(cand)
            if student:
                return [Atom("Student", (Constant(student),))], f"Student({student})"
            words = [w.capitalize() for w in cand.split() if w]
            norm_name = "".join(words) if words else cand.capitalize()
            return [Atom("Student", (Constant(norm_name),))], f"Student({norm_name})"

    # Pattern 22: "Who are the students?" / "List students"
    if re.search(r"\b(?:who are the students|list (?:all )?students)\b", q_lower):
        return [Atom("Student", (Variable("x"),))], "Student(x)"

    # Pattern 23: "Who are the professors?" / "List professors"
    if re.search(r"\b(?:who are the professors|list (?:all )?professors|who are the faculty)\b", q_lower):
        return [Atom("Professor", (Variable("x"),))], "Professor(x)"

    # Pattern 24: "What are the courses?" / "List courses"
    if re.search(r"\b(?:what are the courses|list (?:all )?courses)\b", q_lower):
        return [Atom("Course", (Variable("x"),))], "Course(x)"

    # Pattern 25: "What are the departments?" / "List departments"
    if re.search(r"\b(?:what are the departments|list (?:all )?departments)\b", q_lower):
        return [Atom("Department", (Variable("x"),))], "Department(x)"

    raise ValueError(
        f"Could not parse question: '{question}'. "
        "Try asking like: 'Who teaches AI?', 'Which students study AI?', "
        "'Is Ravi enrolled in AI?', or enter a direct FOL query like 'Studies(x, AI)'."
    )
