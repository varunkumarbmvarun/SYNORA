from typing import Optional, Dict, Tuple, List, Set
from backend.logic.terms import Term, Constant, Variable, Atom


def walk(term: Term, subst: Dict[Variable, Term]) -> Term:
    """Dereference a term through substitution chains."""
    curr = term
    visited = set()
    while isinstance(curr, Variable) and curr in subst:
        if curr in visited:
            break
        visited.add(curr)
        curr = subst[curr]
    return curr


def apply_subst(term: Term, subst: Dict[Variable, Term]) -> Term:
    """Recursively resolve term under substitution."""
    return walk(term, subst)


def substitute(atom: Atom, subst: Dict[Variable, Term]) -> Atom:
    """Apply substitution to an Atom, returning a new Atom."""
    if not subst:
        return atom
    new_terms = tuple(apply_subst(t, subst) for t in atom.terms)
    return Atom(atom.predicate, new_terms)


def unify_terms(
    t1: Term,
    t2: Term,
    subst: Optional[Dict[Variable, Term]] = None
) -> Optional[Dict[Variable, Term]]:
    """Unify two terms under an accumulated substitution."""
    if subst is None:
        subst = {}

    t1 = walk(t1, subst)
    t2 = walk(t2, subst)

    if t1 == t2:
        return subst

    if isinstance(t1, Variable):
        new_subst = dict(subst)
        new_subst[t1] = t2
        return new_subst

    if isinstance(t2, Variable):
        new_subst = dict(subst)
        new_subst[t2] = t1
        return new_subst

    if isinstance(t1, Constant) and isinstance(t2, Constant):
        if t1.name == t2.name:
            return subst
        return None

    return None


def unify_atoms(
    a1: Atom,
    a2: Atom,
    subst: Optional[Dict[Variable, Term]] = None
) -> Optional[Dict[Variable, Term]]:
    """
    Unify two atoms under an accumulated substitution.
    Returns None if unification is impossible.
    """
    if a1.predicate != a2.predicate:
        return None
    if len(a1.terms) != len(a2.terms):
        return None

    if subst is None:
        subst = {}

    current = dict(subst)
    for t1, t2 in zip(a1.terms, a2.terms):
        current = unify_terms(t1, t2, current)
        if current is None:
            return None
    return current


def unify(
    pattern_atom: Atom,
    ground_atom: Atom,
    subst: Optional[Dict[Variable, Term]] = None
) -> Optional[Dict[Variable, Term]]:
    """Alias for unify_atoms, matching the specification signature."""
    return unify_atoms(pattern_atom, ground_atom, subst)


def match_conjunction(
    body: List[Atom],
    facts_by_pred: Dict[str, List[Atom]],
    subst: Optional[Dict[Variable, Term]] = None,
    matched_so_far: Optional[List[Atom]] = None
) -> List[Tuple[Dict[Variable, Term], List[Atom]]]:
    """
    Find all substitutions and supporting premises that satisfy all body atoms
    against a predicate-indexed fact collection.
    """
    if subst is None:
        subst = {}
    if matched_so_far is None:
        matched_so_far = []

    if not body:
        return [(subst, matched_so_far)]

    first = body[0]
    rest = body[1:]
    first_inst = substitute(first, subst)

    candidates = facts_by_pred.get(first_inst.predicate, [])
    results: List[Tuple[Dict[Variable, Term], List[Atom]]] = []

    for fact in candidates:
        new_subst = unify_atoms(first_inst, fact, dict(subst))
        if new_subst is not None:
            sub_results = match_conjunction(
                rest,
                facts_by_pred,
                new_subst,
                matched_so_far + [fact]
            )
            results.extend(sub_results)

    return results
