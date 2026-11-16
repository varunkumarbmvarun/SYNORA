import pytest
from backend.logic.terms import Constant, Variable, Atom, Rule
from backend.logic.parser import parse_atom, parse_fact, parse_rule, ParseError
from backend.logic.unifier import unify_atoms, substitute
from backend.logic.forward_chaining import ForwardChainingEngine
from backend.logic.backward_chaining import BackwardChainingEngine
from backend.logic.query_parser import EntityCatalog, parse_natural_language_query


def get_seed_rules():
    rules_text = [
        # Predefined 1-10
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
        # Additional 11-15
        (11, "Enrolled implies Student", "∀x ∀y (Enrolled(x,y) → Student(x))"),
        (12, "Enrolled and OfferedBy implies AssociatedWith", "∀x ∀y ∀z (Enrolled(x,y) ∧ OfferedBy(y,z) → AssociatedWith(x,z))"),
        (13, "BelongsTo implies AssociatedWith", "∀x ∀y (BelongsTo(x,y) → AssociatedWith(x,y))"),
        (14, "HeadOf implies BelongsTo", "∀x ∀y (HeadOf(x,y) → BelongsTo(x,y))"),
        (15, "Prerequisite implies Course (y)", "∀x ∀y (Prerequisite(x,y) → Course(y))"),
    ]
    return [parse_rule(txt, name=name, rule_id=rid) for rid, name, txt in rules_text]


def get_seed_facts():
    facts_text = [
        # Departments
        "Department(CSE)", "Department(ISE)", "Department(ECE)",
        # Professors
        "Professor(Meena)", "Professor(Kiran)", "Professor(Anand)",
        "BelongsTo(Meena, CSE)", "BelongsTo(Kiran, CSE)", "BelongsTo(Anand, CSE)",
        "HeadOf(Meena, CSE)",
        # Students
        "Student(Ravi)", "Student(Rahul)", "Student(Priya)", "Student(Arjun)", "Student(Sneha)",
        "BelongsTo(Ravi, CSE)", "BelongsTo(Rahul, CSE)", "BelongsTo(Priya, CSE)",
        "BelongsTo(Arjun, CSE)", "BelongsTo(Sneha, CSE)",
        # Courses & OfferedBy
        "Course(AI)", "Course(DSA)", "Course(DBMS)", "Course(CN)", "Course(ML)",
        "OfferedBy(AI, CSE)", "OfferedBy(DSA, CSE)", "OfferedBy(DBMS, CSE)",
        "OfferedBy(CN, CSE)", "OfferedBy(ML, CSE)",
        # Enrollments
        "Enrolled(Ravi, AI)", "Enrolled(Rahul, AI)", "Enrolled(Priya, DBMS)",
        "Enrolled(Arjun, DSA)", "Enrolled(Sneha, ML)", "Enrolled(Priya, AI)",
        # Teaching
        "Teaches(Meena, AI)", "Teaches(Kiran, DSA)", "Teaches(Anand, DBMS)",
        "Teaches(Kiran, CN)", "Teaches(Meena, ML)",
        # Prerequisites
        "Prerequisite(DSA, AI)", "Prerequisite(AI, ML)"
    ]
    return [parse_fact(f) for f in facts_text]


def test_parser_valid_rules_and_facts():
    r = parse_rule("∀x ∀y (Enrolled(x,y) → Studies(x,y))", name="Rule 1", rule_id=1)
    assert r.head.predicate == "Studies"
    assert len(r.body) == 1
    assert r.body[0].predicate == "Enrolled"

    # Multi-premise rule
    r2 = parse_rule("Enrolled(x,y) & Teaches(z,y) -> AssociatedWith(x,z)", name="Rule Custom")
    assert len(r2.body) == 2
    assert r2.head.predicate == "AssociatedWith"

    # Ground fact
    f = parse_fact("Enrolled(Ravi, AI)")
    assert f.is_ground()
    assert f.terms[0].name == "Ravi"
    assert f.terms[1].name == "AI"


def test_parser_invalid_predicates_and_arity():
    with pytest.raises(ParseError):
        parse_atom("UnknownPredicate(Ravi)")

    with pytest.raises(ParseError):
        # Enrolled requires arity 2
        parse_atom("Enrolled(Ravi)")

    with pytest.raises(ParseError):
        # Fact cannot contain variables
        parse_fact("Enrolled(x, AI)")

    with pytest.raises(ParseError):
        # Safety condition violation: z in head is not in body
        parse_rule("Enrolled(x, y) -> AssociatedWith(x, z)")


def test_forward_chaining():
    rules = get_seed_rules()
    base_facts = get_seed_facts()

    engine = ForwardChainingEngine(rules)
    result = engine.run(base_facts)

    derived_strs = {d["fact"] for d in result["newly_inferred_facts"]}

    # Acceptance test 1 checks:
    # Studies(Ravi, AI), Studies(Rahul, AI), Studies(Priya, DBMS), Faculty(Meena), AssociatedWith(Ravi, CSE)
    assert "Studies(Ravi, AI)" in derived_strs
    assert "Studies(Rahul, AI)" in derived_strs
    assert "Studies(Priya, DBMS)" in derived_strs
    assert "Faculty(Meena)" in derived_strs
    assert "AssociatedWith(Ravi, CSE)" in derived_strs

    # Second run on all facts must derive 0 new facts
    all_facts = result["all_facts"]
    result2 = engine.run(all_facts)
    assert result2["new_facts_count"] == 0


def test_backward_chaining_basic():
    rules = get_seed_rules()
    base_facts = get_seed_facts()

    engine = BackwardChainingEngine(rules, base_facts)

    # Acceptance test 2: prove Studies(Ravi, AI) = TRUE before forward chaining
    goal = parse_atom("Studies(Ravi, AI)")
    res = engine.prove_goal(goal)
    assert res["truth_value"] == "TRUE"
    assert res["proof_tree"]["status"] == "PROVED"
    assert res["proof_tree"]["rule_id"] == 1

    # Acceptance test 3: Studies(Ravi, DBMS) = FALSE; Studies(Ghost, AI) = UNKNOWN
    goal_false = parse_atom("Studies(Ravi, DBMS)")
    res_false = engine.prove_goal(goal_false)
    assert res_false["truth_value"] == "FALSE"

    goal_unknown = parse_atom("Studies(Ghost, AI)")
    res_unknown = engine.prove_goal(goal_unknown)
    assert res_unknown["truth_value"] == "UNKNOWN"


def test_backward_chaining_variable_goal():
    rules = get_seed_rules()
    base_facts = get_seed_facts()

    engine = BackwardChainingEngine(rules, base_facts)

    # "Which students study AI?" -> Studies(x, AI)
    goal = parse_atom("Studies(x, AI)")
    res = engine.prove_goal(goal)
    assert res["truth_value"] == "TRUE"
    students = {b["x"] for b in res["bindings"]}
    # In seed facts: Ravi, Rahul, and Priya are enrolled in AI
    assert "Ravi" in students
    assert "Rahul" in students
    assert "Priya" in students


def test_rule_toggle_effect():
    rules = get_seed_rules()
    base_facts = get_seed_facts()

    # Acceptance test 5: Disabling Rule 1 makes Studies(Ravi, AI) FALSE; re-enabling restores TRUE
    active_rules = [r for r in rules if r.rule_id != 1]
    engine_disabled = BackwardChainingEngine(active_rules, base_facts)
    res_disabled = engine_disabled.prove_goal(parse_atom("Studies(Ravi, AI)"))
    assert res_disabled["truth_value"] == "FALSE"

    engine_enabled = BackwardChainingEngine(rules, base_facts)
    res_enabled = engine_enabled.prove_goal(parse_atom("Studies(Ravi, AI)"))
    assert res_enabled["truth_value"] == "TRUE"


def test_custom_rule():
    # Acceptance test 6: custom rule Teaches(x,y) & Enrolled(z,y) -> AssociatedWith(z,x)
    custom_rule = parse_rule(
        "Teaches(x,y) & Enrolled(z,y) -> AssociatedWith(z,x)",
        name="Student associated with professor",
        rule_id=99
    )
    base_facts = get_seed_facts()
    engine = ForwardChainingEngine([custom_rule])
    res = engine.run(base_facts)

    derived = {d["fact"] for d in res["newly_inferred_facts"]}
    # Ravi enrolled in AI, Meena teaches AI -> AssociatedWith(Ravi, Meena)
    assert "AssociatedWith(Ravi, Meena)" in derived


def test_query_parser_nlp():
    catalog = EntityCatalog(
        students=["Ravi", "Rahul", "Priya", "Arjun", "Sneha"],
        professors=["Meena", "Kiran", "Anand"],
        courses={"AI": "AI", "Artificial Intelligence": "AI", "Machine Learning": "ML"},
        departments={"CSE": "CSE"}
    )

    atoms, disp = parse_natural_language_query("Who teaches Artificial Intelligence?", catalog)
    assert disp == "Teaches(x, AI)"

    atoms, disp = parse_natural_language_query("Which students study AI?", catalog)
    assert disp == "Studies(x, AI)"

    atoms, disp = parse_natural_language_query("Is Ravi enrolled in AI?", catalog)
    assert disp == "Enrolled(Ravi, AI)"

    atoms, disp = parse_natural_language_query("Who is Ravi's professor?", catalog)
    assert disp == "Studies(Ravi, y) ∧ Teaches(x, y)"
