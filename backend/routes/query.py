from flask import Blueprint, request
from backend.database import db_session
from backend.models import (
    Student, Professor, Course, Department, Fact, Rule, QueryHistory
)
from backend.logic.terms import Atom, Constant
from backend.logic.parser import parse_rule
from backend.logic.backward_chaining import BackwardChainingEngine
from backend.logic.query_parser import EntityCatalog, parse_natural_language_query
from backend.logic.explain import build_explanation
from backend.services.sync_service import SyncService
from backend.routes.utils import success_response, error_response

query_bp = Blueprint('query', __name__, url_prefix='/api/query')


def _build_live_catalog(session) -> EntityCatalog:
    students = [s.name for s in session.query(Student).all()]
    professors = [p.name for p in session.query(Professor).all()]

    courses = {}
    for c in session.query(Course).all():
        courses[c.alias] = c.alias
        courses[c.name] = c.alias
        courses[c.course_code] = c.alias

    departments = {}
    for d in session.query(Department).all():
        departments[d.code] = d.code
        departments[d.name] = d.code
        if d.code in ("ISE", "IS"):
            departments["IS"] = d.code
            departments["ISE"] = d.code
            departments["Information Science"] = d.code
        elif d.code == "ECE":
            departments["Electronics"] = d.code

    return EntityCatalog(
        students=students,
        professors=professors,
        courses=courses,
        departments=departments
    )


def _load_engine(session):
    rules_db = session.query(Rule).filter(Rule.enabled == True).all()
    parsed_rules = []
    for r in rules_db:
        try:
            parsed = parse_rule(r.rule_text, name=r.name, rule_id=r.id)
            parsed_rules.append(parsed)
        except Exception:
            pass

    facts_db = session.query(Fact).all()
    parsed_facts = []
    for f in facts_db:
        terms = [Constant(f.arg1)]
        if f.arg2:
            terms.append(Constant(f.arg2))
        atom = Atom(f.predicate, tuple(terms))
        parsed_facts.append(atom)

    return BackwardChainingEngine(parsed_rules, parsed_facts)


@query_bp.route('', methods=['POST'])
def execute_query():
    session = db_session()
    data = request.get_json() or {}
    question = data.get('question', '').strip()

    if not question:
        return error_response("Missing 'question' in request body", status_code=400)

    catalog = _build_live_catalog(session)

    try:
        atoms, logical_query = parse_natural_language_query(question, catalog)
    except ValueError as e:
        return error_response(
            str(e),
            code="QUERY_PARSE_ERROR",
            details={
                "suggestions": [
                    "Who teaches AI?",
                    "Which students study AI?",
                    "Which professors belong to CSE?",
                    "Which courses are offered by CSE?",
                    "Who is the head of CSE?",
                    "Is Ravi enrolled in AI?",
                    "Is Meena a professor?",
                    "Is Ravi associated with CSE?",
                    "What are the prerequisites of ML?",
                    "Who is Ravi's professor?"
                ]
            },
            status_code=422
        )

    engine = _load_engine(session)

    if len(atoms) == 1:
        res = engine.prove_goal(atoms[0])
    else:
        res = engine.prove_conjunction_query(atoms)

    truth_val = res["truth_value"]
    bindings = res.get("bindings", [])
    proof_tree = res.get("proof_tree", {})
    matching_facts = res.get("matching_facts", [])
    rules_applied = res.get("rules_applied", [])
    exec_ms = res.get("execution_ms", 0.0)

    # Extract answers from bindings
    answers = []
    seen = set()
    for b in bindings:
        # If there is variable 'x', prioritize it, else all values
        if 'x' in b:
            val = b['x']
            if val not in seen:
                seen.add(val)
                answers.append(val)
        else:
            joined_val = ", ".join(f"{k}={v}" for k, v in b.items())
            if joined_val not in seen:
                seen.add(joined_val)
                answers.append(joined_val)

    # If truth is TRUE and there were no variables (ground query), answer is "Yes, it holds."
    if not answers and truth_val == "TRUE":
        first_atom = atoms[0]
        if first_atom.predicate == "Student":
            answers = [f"{first_atom.terms[0].name} is a Student."]
        elif first_atom.predicate == "Professor":
            answers = [f"{first_atom.terms[0].name} is a Professor."]
        else:
            answers = ["Yes, it holds."]
    elif not answers and truth_val == "FALSE":
        answers = ["No, it does not hold."]
    elif not answers and truth_val == "UNKNOWN":
        answers = ["Unknown / entity not found in the Knowledge Base."]

    explanation = build_explanation(
        question=question,
        logical_query=logical_query,
        truth_value=truth_val,
        answers=answers if truth_val == "TRUE" and len(atoms[0].variables()) > 0 else [],
        matching_facts=matching_facts,
        rules_applied=rules_applied,
        proof_tree=proof_tree
    )

    # Save to history
    history_entry = QueryHistory(
        question=question,
        logical_query=logical_query,
        answer=", ".join(answers),
        truth_value=truth_val,
        matching_facts=matching_facts,
        rules_applied=rules_applied,
        trace=proof_tree
    )
    session.add(history_entry)
    SyncService.log_activity(session, "QUERY", "NLP", f"Query '{question}' -> {truth_val}")
    session.commit()

    result_payload = {
        "id": history_entry.id,
        "question": question,
        "logical_query": logical_query,
        "truth_value": truth_val,
        "answers": answers,
        "matching_facts": matching_facts,
        "rules_applied": rules_applied,
        "proof_tree": proof_tree,
        "explanation": explanation,
        "execution_ms": exec_ms
    }

    return success_response(result_payload, message="Query executed successfully")


@query_bp.route('/history', methods=['GET'])
def get_query_history():
    session = db_session()
    limit = int(request.args.get('limit', 50))
    history = session.query(QueryHistory).order_by(QueryHistory.id.desc()).limit(limit).all()
    return success_response([h.to_dict() for h in history])


@query_bp.route('/history', methods=['DELETE'])
def clear_query_history():
    session = db_session()
    count = session.query(QueryHistory).delete()
    session.commit()
    return success_response({"deleted_count": count}, message="Query history cleared")
