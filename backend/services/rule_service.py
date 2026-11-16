from typing import Dict, Any, List, Optional
from collections import defaultdict
from sqlalchemy.orm import Session
from backend.models import Rule, Fact
from backend.logic.parser import parse_rule, ParseError
from backend.logic.terms import Atom, Constant
from backend.logic.unifier import match_conjunction, substitute
from backend.services.sync_service import SyncService


class RuleService:
    @staticmethod
    def get_rules(session: Session) -> List[Dict[str, Any]]:
        rules = session.query(Rule).order_by(Rule.id).all()
        return [r.to_dict() for r in rules]

    @staticmethod
    def get_rule_by_id(session: Session, rule_id: int) -> Optional[Rule]:
        return session.get(Rule, rule_id)

    @staticmethod
    def create_rule(
        session: Session,
        name: str,
        rule_text: str,
        is_custom: bool = True,
        enabled: bool = True
    ) -> Rule:
        name = name.strip()
        rule_text = rule_text.strip()
        if not name:
            raise ValueError("Rule name cannot be empty.")
        if not rule_text:
            raise ValueError("Rule text cannot be empty.")

        try:
            parsed = parse_rule(rule_text, name=name)
        except ParseError as e:
            raise ValueError(str(e))

        rule = Rule(
            name=name,
            rule_text=str(parsed),
            is_custom=is_custom,
            enabled=enabled
        )
        session.add(rule)
        session.flush()

        SyncService.log_activity(session, "CREATE", "Rule", f"Created rule '{name}': {str(parsed)}")
        return rule

    @staticmethod
    def update_rule(
        session: Session,
        rule_id: int,
        name: Optional[str] = None,
        rule_text: Optional[str] = None,
        enabled: Optional[bool] = None
    ) -> Rule:
        rule = session.get(Rule, rule_id)
        if not rule:
            raise ValueError(f"Rule with ID {rule_id} not found.")

        if name is not None:
            rule.name = name.strip()

        if enabled is not None:
            rule.enabled = enabled

        if rule_text is not None and rule_text.strip():
            try:
                parsed = parse_rule(rule_text.strip(), name=rule.name, rule_id=rule.id)
                rule.rule_text = str(parsed)
            except ParseError as e:
                raise ValueError(str(e))

        session.flush()
        status_str = "enabled" if rule.enabled else "disabled"
        SyncService.log_activity(session, "UPDATE", "Rule", f"Updated rule {rule.id} ({rule.name}) -> {status_str}")
        return rule

    @staticmethod
    def delete_rule(session: Session, rule_id: int) -> bool:
        rule = session.get(Rule, rule_id)
        if not rule:
            raise ValueError(f"Rule with ID {rule_id} not found.")

        if not rule.is_custom:
            raise ValueError(
                f"Cannot delete predefined system rule '{rule.name}'. "
                "You may disable it instead."
            )

        session.delete(rule)
        SyncService.log_activity(session, "DELETE", "Rule", f"Deleted custom rule '{rule.name}' (ID {rule_id})")
        return True

    @staticmethod
    def test_rule(session: Session, rule_text: str) -> Dict[str, Any]:
        """
        Dry-run a rule against existing facts in the DB.
        Does not mutate the database.
        """
        try:
            rule = parse_rule(rule_text)
        except ParseError as e:
            raise ValueError(str(e))

        # Fetch facts
        facts_db = session.query(Fact).all()
        known_facts = set()
        facts_by_pred = defaultdict(list)

        for f in facts_db:
            terms = [Constant(f.arg1)]
            if f.arg2:
                terms.append(Constant(f.arg2))
            atom = Atom(f.predicate, tuple(terms))
            known_facts.add(atom)
            facts_by_pred[f.predicate].append(atom)

        matches = match_conjunction(rule.body, facts_by_pred)

        results = []
        derived_facts = []
        seen_derived = set()

        for subst, premises in matches:
            head_inst = substitute(rule.head, subst)
            head_str = str(head_inst)
            is_new = head_inst not in known_facts

            item = {
                "substitution": {str(k): str(v) for k, v in subst.items()},
                "premises": [str(p) for p in premises],
                "head": head_str,
                "is_already_known": not is_new
            }
            results.append(item)

            if is_new and head_str not in seen_derived:
                seen_derived.add(head_str)
                derived_facts.append(head_str)

        return {
            "parsed_rule": str(rule),
            "total_matches": len(matches),
            "new_facts_count": len(derived_facts),
            "new_facts": derived_facts,
            "details": results[:50]
        }
