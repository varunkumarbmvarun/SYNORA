from flask import Blueprint, request
from backend.database import db_session
from backend.models import Rule, Fact, InferenceResult
from backend.logic.terms import Atom, Constant
from backend.logic.parser import parse_rule, parse_atom, ATOM_PATTERN, ParseError
from backend.logic.forward_chaining import ForwardChainingEngine
from backend.logic.backward_chaining import BackwardChainingEngine
from backend.services.sync_service import SyncService
from backend.services.fact_service import FactService
from backend.routes.utils import success_response, error_response

inference_bp = Blueprint('inference', __name__, url_prefix='/api/inference')


def _load_enabled_rules(session):
    rules_db = session.query(Rule).filter(Rule.enabled == True).all()
    parsed_rules = []
    for r in rules_db:
        try:
            parsed = parse_rule(r.rule_text, name=r.name, rule_id=r.id)
            parsed_rules.append(parsed)
        except Exception:
            pass
    return parsed_rules


def _load_base_facts(session):
    facts_db = session.query(Fact).all()
    parsed_facts = []
    for f in facts_db:
        terms = [Constant(f.arg1)]
        if f.arg2:
            terms.append(Constant(f.arg2))
        atom = Atom(f.predicate, tuple(terms))
        parsed_facts.append(atom)
    return parsed_facts


@inference_bp.route('/forward', methods=['POST'])
def run_forward_chaining():
    session = db_session()
    parsed_rules = _load_enabled_rules(session)
    parsed_facts = _load_base_facts(session)

    engine = ForwardChainingEngine(parsed_rules)
    result = engine.run(parsed_facts)

    # Persist newly derived facts
    newly_added_count = 0
    for item in result["newly_inferred_facts"]:
        try:
            FactService.get_or_create_fact = SyncService.get_or_create_fact
            SyncService.get_or_create_fact(
                session=session,
                predicate=item["predicate"],
                arg1=item["arg1"],
                arg2=item["arg2"],
                source="inference",
                is_inferred=True,
                source_rule_id=item.get("rule_id")
            )
            newly_added_count += 1
        except Exception:
            pass

    # Save inference result
    applied_rules = [{"id": r.rule_id, "name": r.name, "text": str(r)} for r in parsed_rules]
    inf_record = InferenceResult(
        run_type="forward",
        goal=None,
        iterations=result["iterations"],
        new_facts_count=result["new_facts_count"],
        rules_applied=applied_rules,
        steps=result["steps"],
        execution_ms=result["execution_ms"]
    )
    session.add(inf_record)
    SyncService.log_activity(
        session,
        "INFERENCE",
        "Engine",
        f"Forward chaining ran: {result['iterations']} iterations, {result['new_facts_count']} new facts derived in {result['execution_ms']}ms"
    )
    session.commit()

    return success_response({
        "inference_id": inf_record.id,
        "original_fact_count": result["original_fact_count"],
        "total_facts_after": result["total_facts_after"],
        "new_facts_count": result["new_facts_count"],
        "iterations": result["iterations"],
        "execution_ms": result["execution_ms"],
        "steps": result["steps"],
        "newly_inferred_facts": result["newly_inferred_facts"]
    }, message=f"Forward chaining completed: {result['new_facts_count']} facts derived.")


@inference_bp.route('/backward', methods=['POST'])
def run_backward_chaining():
    session = db_session()
    data = request.get_json() or {}
    goal_str = data.get('goal', '').strip()

    if not goal_str:
        return error_response("Missing 'goal' in request body", status_code=400)

    try:
        # Check if single atom or conjunction
        cleaned = goal_str.replace('∧', '&').replace('AND', '&')
        atom_strings = [m.group(0) for m in ATOM_PATTERN.finditer(cleaned)]
        if not atom_strings:
            return error_response(f"Could not parse goal atom: '{goal_str}'", status_code=422)

        goals = [parse_atom(s, allow_variables=True) for s in atom_strings]
    except ParseError as e:
        return error_response(str(e), code="PARSE_ERROR", status_code=422)

    parsed_rules = _load_enabled_rules(session)
    parsed_facts = _load_base_facts(session)

    engine = BackwardChainingEngine(parsed_rules, parsed_facts)

    if len(goals) == 1:
        res = engine.prove_goal(goals[0])
    else:
        res = engine.prove_conjunction_query(goals)

    # Save inference record
    inf_record = InferenceResult(
        run_type="backward",
        goal=goal_str,
        iterations=1,
        new_facts_count=len(res.get("matching_facts", [])),
        rules_applied=res.get("rules_applied", []),
        steps=[{"goal": goal_str, "status": res["truth_value"]}],
        execution_ms=res["execution_ms"]
    )
    session.add(inf_record)
    SyncService.log_activity(
        session,
        "INFERENCE",
        "Engine",
        f"Backward chaining proved '{goal_str}' -> {res['truth_value']} in {res['execution_ms']}ms"
    )
    session.commit()

    res["inference_id"] = inf_record.id
    return success_response(res, message=f"Backward chaining proof: {res['truth_value']}")


@inference_bp.route('/results', methods=['GET'])
def list_inference_results():
    session = db_session()
    limit = int(request.args.get('limit', 20))
    results = session.query(InferenceResult).order_by(InferenceResult.id.desc()).limit(limit).all()
    return success_response([r.to_dict() for r in results])


@inference_bp.route('/inferred', methods=['DELETE'])
def clear_inferred():
    session = db_session()
    count = FactService.clear_inferred_facts(session)
    session.commit()
    return success_response({"deleted_count": count}, message=f"Cleared {count} inferred facts")
