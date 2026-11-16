import time
from typing import List, Dict, Set, Any, Optional, Tuple, Union
from collections import defaultdict
from backend.logic.terms import Term, Constant, Variable, Atom, Rule
from backend.logic.unifier import unify_atoms, substitute, walk


class ProofNode:
    def __init__(
        self,
        goal: str,
        status: str,  # PROVED, FAILED, UNKNOWN
        method: str = "failed",  # fact, rule, failed
        rule_id: Optional[int] = None,
        rule_name: Optional[str] = None,
        rule_text: Optional[str] = None,
        fact_matched: Optional[str] = None,
        substitution: Optional[Dict[str, str]] = None,
        children: Optional[List['ProofNode']] = None
    ):
        self.goal = goal
        self.status = status
        self.method = method
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.rule_text = rule_text
        self.fact_matched = fact_matched
        self.substitution = substitution or {}
        self.children = children or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "status": self.status,
            "method": self.method,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "rule_text": self.rule_text,
            "fact_matched": self.fact_matched,
            "substitution": self.substitution,
            "children": [c.to_dict() for c in self.children]
        }


class BackwardChainingEngine:
    def __init__(
        self,
        rules: List[Rule],
        facts: List[Atom],
        known_entities: Optional[Set[str]] = None,
        max_depth: int = 10
    ):
        self.rules = rules
        self.facts = facts
        self.max_depth = max_depth
        self.var_counter = 0

        # Index facts by predicate
        self.facts_by_pred: Dict[str, List[Atom]] = defaultdict(list)
        self.all_known_entities: Set[str] = set()
        if known_entities:
            self.all_known_entities.update(known_entities)

        for f in facts:
            self.facts_by_pred[f.predicate].append(f)
            for t in f.terms:
                if isinstance(t, Constant):
                    self.all_known_entities.add(t.name)

    def _fresh_rule(self, rule: Rule) -> Rule:
        self.var_counter += 1
        return rule.standardize_apart(self.var_counter)

    def has_unknown_entities(self, atom: Atom) -> bool:
        for t in atom.terms:
            if isinstance(t, Constant) and t.name not in self.all_known_entities:
                return True
        return False

    def prove_goal(self, goal: Atom) -> Dict[str, Any]:
        """
        Prove a single goal (which may contain variables).
        Returns status ('TRUE', 'FALSE', or 'UNKNOWN'), bindings list,
        best proof tree, and execution metrics.
        """
        start_time = time.perf_counter()

        # Check unknown entities in query
        if self.has_unknown_entities(goal):
            node = ProofNode(
                goal=str(goal),
                status="UNKNOWN",
                method="failed",
                fact_matched=None
            )
            return {
                "truth_value": "UNKNOWN",
                "bindings": [],
                "proof_tree": node.to_dict(),
                "matching_facts": [],
                "rules_applied": [],
                "execution_ms": round((time.perf_counter() - start_time) * 1000, 2)
            }

        # Find all successful proofs
        solutions: List[Tuple[Dict[Variable, Term], ProofNode, List[Atom], List[Rule]]] = []
        visited_ancestors: Set[str] = set()

        self._solve_atom(
            goal=goal,
            subst={},
            depth=0,
            visited=visited_ancestors,
            solutions=solutions
        )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        if solutions:
            # We have at least one proof
            # Collect unique answer bindings for variables in goal
            goal_vars = goal.variables()
            bindings_list = []
            seen_bindings = set()

            for subst, pnode, m_facts, r_applied in solutions:
                binding_dict = {}
                for v in sorted(goal_vars, key=lambda x: x.name):
                    val = walk(v, subst)
                    binding_dict[v.name] = val.name if isinstance(val, Constant) else str(val)
                # Key for deduplication
                b_key = tuple(sorted(binding_dict.items()))
                if b_key not in seen_bindings:
                    seen_bindings.add(b_key)
                    if binding_dict:
                        bindings_list.append(binding_dict)

            # Aggregate matching facts & rules applied across best solutions
            all_matching_facts = []
            seen_f = set()
            for _, _, m_facts, _ in solutions:
                for f in m_facts:
                    f_str = str(f)
                    if f_str not in seen_f:
                        seen_f.add(f_str)
                        all_matching_facts.append({"fact": f_str, "inferred": False})

            all_rules_applied = []
            seen_r = set()
            for _, _, _, r_applied in solutions:
                for r in r_applied:
                    if r.rule_id not in seen_r:
                        seen_r.add(r.rule_id)
                        all_rules_applied.append({"id": r.rule_id, "name": r.name, "text": str(r)})

            best_tree = solutions[0][1].to_dict()

            return {
                "truth_value": "TRUE",
                "bindings": bindings_list,
                "proof_tree": best_tree,
                "matching_facts": all_matching_facts,
                "rules_applied": all_rules_applied,
                "execution_ms": elapsed_ms
            }
        else:
            # Closed world assumption: known entities, but no proof found
            failed_tree = ProofNode(
                goal=str(goal),
                status="FALSE",
                method="failed"
            ).to_dict()

            return {
                "truth_value": "FALSE",
                "bindings": [],
                "proof_tree": failed_tree,
                "matching_facts": [],
                "rules_applied": [],
                "execution_ms": elapsed_ms
            }

    def _solve_atom(
        self,
        goal: Atom,
        subst: Dict[Variable, Term],
        depth: int,
        visited: Set[str],
        solutions: List[Tuple[Dict[Variable, Term], ProofNode, List[Atom], List[Rule]]]
    ):
        if depth > self.max_depth:
            return

        inst_goal = substitute(goal, subst)
        goal_key = str(inst_goal)

        # Loop protection
        if goal_key in visited:
            return

        new_visited = visited | {goal_key}

        # 1. Fact matching
        candidates = self.facts_by_pred.get(inst_goal.predicate, [])
        for fact in candidates:
            unified = unify_atoms(inst_goal, fact, dict(subst))
            if unified is not None:
                leaf_node = ProofNode(
                    goal=str(inst_goal),
                    status="PROVED",
                    method="fact",
                    fact_matched=str(fact),
                    substitution={v.name: str(walk(v, unified)) for v in inst_goal.variables()}
                )
                solutions.append((unified, leaf_node, [fact], []))

        # 2. Rule matching
        for rule in self.rules:
            # Standardize apart
            fresh_r = self._fresh_rule(rule)
            unified_head = unify_atoms(inst_goal, fresh_r.head, dict(subst))
            if unified_head is not None:
                # Recursively prove all body atoms in fresh_r
                body_solutions: List[Tuple[Dict[Variable, Term], List[ProofNode], List[Atom], List[Rule]]] = []
                self._solve_conjunction(
                    goals=fresh_r.body,
                    subst=unified_head,
                    depth=depth + 1,
                    visited=new_visited,
                    body_solutions=body_solutions
                )

                for final_subst, child_nodes, matched_facts, rules_in_branch in body_solutions:
                    rule_node = ProofNode(
                        goal=str(inst_goal),
                        status="PROVED",
                        method="rule",
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        rule_text=str(rule),
                        substitution={v.name: str(walk(v, final_subst)) for v in inst_goal.variables()},
                        children=child_nodes
                    )
                    solutions.append((
                        final_subst,
                        rule_node,
                        matched_facts,
                        [rule] + rules_in_branch
                    ))

    def _solve_conjunction(
        self,
        goals: List[Atom],
        subst: Dict[Variable, Term],
        depth: int,
        visited: Set[str],
        body_solutions: List[Tuple[Dict[Variable, Term], List[ProofNode], List[Atom], List[Rule]]]
    ):
        if not goals:
            body_solutions.append((subst, [], [], []))
            return

        first_goal = goals[0]
        rest_goals = goals[1:]

        first_solutions: List[Tuple[Dict[Variable, Term], ProofNode, List[Atom], List[Rule]]] = []
        self._solve_atom(
            goal=first_goal,
            subst=subst,
            depth=depth,
            visited=visited,
            solutions=first_solutions
        )

        for next_subst, node, facts_1, rules_1 in first_solutions:
            rest_solutions: List[Tuple[Dict[Variable, Term], List[ProofNode], List[Atom], List[Rule]]] = []
            self._solve_conjunction(
                goals=rest_goals,
                subst=next_subst,
                depth=depth,
                visited=visited,
                body_solutions=rest_solutions
            )
            for final_subst, rest_nodes, facts_rest, rules_rest in rest_solutions:
                body_solutions.append((
                    final_subst,
                    [node] + rest_nodes,
                    facts_1 + facts_rest,
                    rules_1 + rules_rest
                ))

    def prove_conjunction_query(self, goals: List[Atom]) -> Dict[str, Any]:
        """Prove a conjunction of goals, e.g. Studies(Ravi, y) ∧ Teaches(x, y)."""
        start_time = time.perf_counter()

        for g in goals:
            if self.has_unknown_entities(g):
                node = ProofNode(
                    goal=" ∧ ".join(str(x) for x in goals),
                    status="UNKNOWN",
                    method="failed"
                )
                return {
                    "truth_value": "UNKNOWN",
                    "bindings": [],
                    "proof_tree": node.to_dict(),
                    "matching_facts": [],
                    "rules_applied": [],
                    "execution_ms": round((time.perf_counter() - start_time) * 1000, 2)
                }

        body_solutions: List[Tuple[Dict[Variable, Term], List[ProofNode], List[Atom], List[Rule]]] = []
        self._solve_conjunction(
            goals=goals,
            subst={},
            depth=0,
            visited=set(),
            body_solutions=body_solutions
        )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        if body_solutions:
            all_vars: Set[Variable] = set()
            for g in goals:
                all_vars.update(g.variables())

            bindings_list = []
            seen_bindings = set()

            for subst, child_nodes, m_facts, r_applied in body_solutions:
                binding_dict = {}
                for v in sorted(all_vars, key=lambda x: x.name):
                    val = walk(v, subst)
                    binding_dict[v.name] = val.name if isinstance(val, Constant) else str(val)
                b_key = tuple(sorted(binding_dict.items()))
                if b_key not in seen_bindings:
                    seen_bindings.add(b_key)
                    if binding_dict:
                        bindings_list.append(binding_dict)

            all_matching_facts = []
            seen_f = set()
            for _, _, m_facts, _ in body_solutions:
                for f in m_facts:
                    f_str = str(f)
                    if f_str not in seen_f:
                        seen_f.add(f_str)
                        all_matching_facts.append({"fact": f_str, "inferred": False})

            all_rules_applied = []
            seen_r = set()
            for _, _, _, r_applied in body_solutions:
                for r in r_applied:
                    if r.rule_id not in seen_r:
                        seen_r.add(r.rule_id)
                        all_rules_applied.append({"id": r.rule_id, "name": r.name, "text": str(r)})

            root_tree = {
                "goal": " ∧ ".join(str(g) for g in goals),
                "status": "PROVED",
                "method": "conjunction",
                "children": [node.to_dict() for node in body_solutions[0][1]]
            }

            return {
                "truth_value": "TRUE",
                "bindings": bindings_list,
                "proof_tree": root_tree,
                "matching_facts": all_matching_facts,
                "rules_applied": all_rules_applied,
                "execution_ms": elapsed_ms
            }
        else:
            failed_tree = {
                "goal": " ∧ ".join(str(g) for g in goals),
                "status": "FALSE",
                "method": "failed",
                "children": []
            }
            return {
                "truth_value": "FALSE",
                "bindings": [],
                "proof_tree": failed_tree,
                "matching_facts": [],
                "rules_applied": [],
                "execution_ms": elapsed_ms
            }
