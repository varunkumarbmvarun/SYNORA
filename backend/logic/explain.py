from typing import Dict, Any, List


def format_proof_tree_text(node: Dict[str, Any], indent: int = 0) -> str:
    """Format a proof tree node as indented human-readable text."""
    prefix = "  " * indent
    status = node.get("status", "")
    method = node.get("method", "")
    goal = node.get("goal", "")

    if method == "fact":
        fact = node.get("fact_matched", goal)
        line = f"{prefix}├─ Goal: {goal} -> Proved by known fact '{fact}'\n"
    elif method == "rule":
        r_name = node.get("rule_name") or f"Rule {node.get('rule_id')}"
        r_text = node.get("rule_text", "")
        line = f"{prefix}├─ Goal: {goal} -> Proved via {r_name} [{r_text}]\n"
    elif method == "conjunction":
        line = f"{prefix}├─ Conjunction: {goal} -> Proved all clauses\n"
    else:
        line = f"{prefix}├─ Goal: {goal} -> [{status}]\n"

    children = node.get("children", [])
    for child in children:
        line += format_proof_tree_text(child, indent + 1)
    return line


def build_explanation(
    question: str,
    logical_query: str,
    truth_value: str,
    answers: List[str],
    matching_facts: List[Dict[str, Any]],
    rules_applied: List[Dict[str, Any]],
    proof_tree: Dict[str, Any]
) -> str:
    """Generate a clean, precise explanation of why the query holds or fails."""
    if truth_value == "UNKNOWN":
        return (
            f"The query '{question}' references entities or terms that are not present "
            f"in the College Knowledge Base. Under our open/closed scope boundary, "
            f"the truth value cannot be determined (UNKNOWN)."
        )

    if truth_value == "FALSE":
        return (
            f"No logical proof could be derived for '{logical_query}'. "
            f"Under the Closed-World Assumption (CWA), statements not provable from "
            f"known facts and enabled rules are considered FALSE."
        )

    # TRUE cases
    rules_count = len(rules_applied)
    facts_count = len(matching_facts)

    facts_str = ", ".join(f.get("fact", "") for f in matching_facts[:3])
    if len(matching_facts) > 3:
        facts_str += f", and {len(matching_facts) - 3} more"

    if answers:
        answers_str = ", ".join(answers)
        if rules_count > 0:
            rule_names = ", ".join(r.get("name") or f"Rule {r.get('id')}" for r in rules_applied[:2])
            return (
                f"Result: {answers_str}. "
                f"Satisfied logical query '{logical_query}' using {rule_names} "
                f"grounded in base facts ({facts_str})."
            )
        else:
            return (
                f"Result: {answers_str}. "
                f"Satisfied logical query '{logical_query}' directly matched from base facts ({facts_str})."
            )
    else:
        # Ground question: "Is Ravi enrolled in AI?"
        if rules_count > 0:
            rule_names = ", ".join(r.get("name") or f"Rule {r.get('id')}" for r in rules_applied[:2])
            return (
                f"Holds TRUE: '{logical_query}' was derived via {rule_names} "
                f"supported by known facts: {facts_str}."
            )
        else:
            return f"Holds TRUE: '{logical_query}' is an established fact ({facts_str}) in the knowledge base."
