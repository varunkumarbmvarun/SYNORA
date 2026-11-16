from flask import Blueprint, request
from backend.database import db_session
from backend.models import Fact, Student, Professor, Course, Department
from backend.routes.utils import success_response

graph_bp = Blueprint('graph', __name__, url_prefix='/api/knowledge-graph')


@graph_bp.route('', methods=['GET'])
def get_graph():
    session = db_session()
    predicates_param = request.args.get('predicates')
    include_inferred_param = request.args.get('include_inferred', 'true').lower()
    include_inferred = include_inferred_param in ('true', '1')

    # Load entity maps
    students = {s.name for s in session.query(Student).all()}
    professors = {p.name for p in session.query(Professor).all()}
    courses = {c.alias for c in session.query(Course).all()}
    departments = {d.code for d in session.query(Department).all()}

    q = session.query(Fact)
    if not include_inferred:
        q = q.filter(Fact.is_inferred == False)
    if predicates_param:
        preds = [p.strip() for p in predicates_param.split(',') if p.strip()]
        if preds:
            q = q.filter(Fact.predicate.in_(preds))

    facts = q.all()

    nodes_map = {}
    edges = []

    def get_type(name: str) -> str:
        if name in students:
            return "Student"
        if name in professors:
            return "Professor"
        if name in courses:
            return "Course"
        if name in departments:
            return "Department"
        return "Entity"

    for f in facts:
        # If unary fact: e.g. Student(Ravi), Course(AI), Faculty(Meena)
        if not f.arg2:
            n_id = f.arg1
            if n_id not in nodes_map:
                nodes_map[n_id] = {
                    "id": n_id,
                    "label": n_id,
                    "type": get_type(n_id),
                    "unary_predicates": [f.predicate]
                }
            else:
                if f.predicate not in nodes_map[n_id]["unary_predicates"]:
                    nodes_map[n_id]["unary_predicates"].append(f.predicate)
        else:
            # Binary fact: e.g. Enrolled(Ravi, AI)
            src = f.arg1
            dst = f.arg2

            if src not in nodes_map:
                nodes_map[src] = {
                    "id": src,
                    "label": src,
                    "type": get_type(src),
                    "unary_predicates": []
                }
            if dst not in nodes_map:
                nodes_map[dst] = {
                    "id": dst,
                    "label": dst,
                    "type": get_type(dst),
                    "unary_predicates": []
                }

            edges.append({
                "id": f.id,
                "source": src,
                "target": dst,
                "predicate": f.predicate,
                "label": f.predicate,
                "is_inferred": f.is_inferred
            })

    return success_response({
        "nodes": list(nodes_map.values()),
        "edges": edges,
        "total_nodes": len(nodes_map),
        "total_edges": len(edges)
    })
