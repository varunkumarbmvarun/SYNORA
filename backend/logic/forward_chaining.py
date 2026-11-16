import time
from typing import List, Dict, Set, Any, Optional
from collections import defaultdict
from backend.logic.terms import Atom, Rule, Constant
from backend.logic.unifier import match_conjunction, substitute


class ForwardChainingEngine:
    def __init__(self, rules: List[Rule], max_iterations: int = 50):
        self.rules = rules
        self.max_iterations = max_iterations

    def run(self, base_facts: List[Atom]) -> Dict[str, Any]:
        """
        Execute forward chaining inference to a fixpoint.
        Returns detailed summary and derivation trace.
        """
        start_time = time.perf_counter()

        known_facts: Set[Atom] = set(base_facts)
        facts_by_pred: Dict[str, List[Atom]] = defaultdict(list)
        for f in base_facts:
            facts_by_pred[f.predicate].append(f)

        newly_inferred: List[Dict[str, Any]] = []
        steps: List[Dict[str, Any]] = []
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1
            iteration_new_facts: List[Atom] = []
            iteration_derivations: List[Dict[str, Any]] = []

            for rule in self.rules:
                matches = match_conjunction(rule.body, facts_by_pred)
                for subst, premises in matches:
                    head_inst = substitute(rule.head, subst)
                    if not head_inst.is_ground():
                        # Safety check: if head isn't ground, skip
                        continue

                    if head_inst not in known_facts:
                        known_facts.add(head_inst)
                        facts_by_pred[head_inst.predicate].append(head_inst)
                        iteration_new_facts.append(head_inst)

                        derivation = {
                            "fact": str(head_inst),
                            "predicate": head_inst.predicate,
                            "arg1": head_inst.terms[0].name,
                            "arg2": head_inst.terms[1].name if len(head_inst.terms) > 1 else None,
                            "rule_id": rule.rule_id,
                            "rule_name": rule.name,
                            "rule_text": str(rule),
                            "premises": [str(p) for p in premises],
                            "substitution": {str(k): str(v) for k, v in subst.items()},
                            "iteration": iteration
                        }
                        iteration_derivations.append(derivation)
                        newly_inferred.append(derivation)

            step_summary = {
                "iteration": iteration,
                "facts_derived_count": len(iteration_new_facts),
                "facts": [str(f) for f in iteration_new_facts]
            }
            steps.append(step_summary)

            if not iteration_new_facts:
                # Fixpoint reached
                break

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "original_fact_count": len(base_facts),
            "total_facts_after": len(known_facts),
            "new_facts_count": len(newly_inferred),
            "iterations": iteration,
            "execution_ms": elapsed_ms,
            "steps": steps,
            "newly_inferred_facts": newly_inferred,
            "all_facts": list(known_facts)
        }
