import re
from typing import List, Tuple, Optional
from backend.logic.terms import (
    Term, Constant, Variable, Atom, Rule,
    ALL_PREDICATES, PREDICATE_ARITY
)

ATOM_PATTERN = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)')

class ParseError(ValueError):
    """Raised when parsing a fact, rule, or atom fails."""
    pass


def parse_term(token: str, allow_variables: bool = True) -> Term:
    token = token.strip()
    if not token:
        raise ParseError("Empty term encountered")
    # If starts with lowercase letter or is single lowercase letter
    if token[0].islower():
        if not allow_variables:
            raise ParseError(f"Fact cannot contain variable '{token}'. Facts must only contain ground constants.")
        return Variable(token)
    return Constant(token)


def parse_atom(atom_str: str, allow_variables: bool = True) -> Atom:
    """Parse a single atom string like 'Enrolled(Ravi, AI)' or 'Studies(x, y)'."""
    atom_str = atom_str.strip()
    match = ATOM_PATTERN.fullmatch(atom_str)
    if not match:
        # Try finding match if whitespace or parentheses wrap it
        matches = list(ATOM_PATTERN.finditer(atom_str))
        if len(matches) == 1 and atom_str.strip().strip("()").strip() == matches[0].group(0):
            match = matches[0]
        else:
            raise ParseError(f"Malformed atom syntax: '{atom_str}'. Expected format: Predicate(arg1, ...)")

    predicate = match.group(1).strip()
    args_raw = match.group(2).strip()

    if predicate not in ALL_PREDICATES:
        raise ParseError(
            f"Unknown predicate '{predicate}'. Allowed predicates: {sorted(ALL_PREDICATES)}"
        )

    expected_arity = PREDICATE_ARITY[predicate]
    if not args_raw:
        args = []
    else:
        args = [a.strip() for a in args_raw.split(',')]

    if len(args) != expected_arity:
        raise ParseError(
            f"Predicate '{predicate}' expects arity {expected_arity}, but got {len(args)} argument(s)"
        )

    terms = tuple(parse_term(arg, allow_variables=allow_variables) for arg in args)
    return Atom(predicate=predicate, terms=terms)


def parse_fact(fact_str: str) -> Atom:
    """Parse a ground fact string like 'Enrolled(Ravi, AI)'. Variables are not allowed in facts."""
    fact_str = fact_str.strip()
    atom = parse_atom(fact_str, allow_variables=False)
    if not atom.is_ground():
        raise ParseError(f"Fact '{fact_str}' contains variables, but facts must be ground constants.")
    return atom


def clean_rule_text(rule_str: str) -> str:
    """Remove quantifier prefixes like ∀x ∀y and outermost parentheses."""
    s = rule_str.strip()
    # Strip quantifiers like ∀x, ∀y, \forall x
    s = re.sub(r'^[∀\\]\s*[a-zA-Z0-9_]+\s*', '', s)
    while re.match(r'^[∀\\]\s*[a-zA-Z0-9_]+', s):
        s = re.sub(r'^[∀\\]\s*[a-zA-Z0-9_]+\s*', '', s)
    s = s.strip()
    # If wrapped in outermost parens, strip
    if s.startswith('(') and s.endswith(')'):
        # Ensure it's a balanced outer pair
        depth = 0
        balanced_outer = True
        for i, ch in enumerate(s):
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0 and i < len(s) - 1:
                    balanced_outer = False
                    break
        if balanced_outer:
            s = s[1:-1].strip()
    return s


def parse_rule(rule_str: str, name: str = "", rule_id: Optional[int] = None) -> Rule:
    """
    Parse a rule string such as:
    - ∀x ∀y (Enrolled(x,y) → Studies(x,y))
    - Enrolled(x,y) -> Studies(x,y)
    - Enrolled(x,y) & Teaches(z,y) -> AssociatedWith(x,z)
    """
    raw_str = rule_str.strip()
    cleaned = clean_rule_text(raw_str)

    # Implication operators: →, ->, =>
    arrow = None
    for op in ['→', '->', '=>']:
        if op in cleaned:
            arrow = op
            break

    if not arrow:
        raise ParseError(f"Rule missing implication arrow ('→', '->', or '=>'): '{rule_str}'")

    parts = cleaned.split(arrow, 1)
    body_part = parts[0].strip()
    head_part = parts[1].strip()

    # Head must be a single atom
    head_matches = list(ATOM_PATTERN.finditer(head_part))
    if not head_matches:
        raise ParseError(f"Rule head could not be parsed: '{head_part}'")
    if len(head_matches) > 1:
        raise ParseError(f"Rule head must contain exactly one atom, found {len(head_matches)}")

    head_atom = parse_atom(head_matches[0].group(0), allow_variables=True)

    # Body can contain multiple atoms separated by ∧, &, AND, or commas outside atom parens
    body_matches = list(ATOM_PATTERN.finditer(body_part))
    if not body_matches:
        raise ParseError(f"Rule body contains no valid atoms: '{body_part}'")

    body_atoms = [parse_atom(m.group(0), allow_variables=True) for m in body_matches]

    try:
        return Rule(head=head_atom, body=body_atoms, name=name, rule_id=rule_id)
    except ValueError as e:
        raise ParseError(str(e))
