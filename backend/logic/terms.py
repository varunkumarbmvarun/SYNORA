from dataclasses import dataclass
from typing import Tuple, List, Set, Union, Optional

UNARY_PREDICATES = {"Student", "Professor", "Course", "Department", "Faculty"}
BINARY_PREDICATES = {
    "Enrolled", "Teaches", "BelongsTo", "OfferedBy",
    "Studies", "HeadOf", "Prerequisite", "AssociatedWith"
}
ALL_PREDICATES = UNARY_PREDICATES | BINARY_PREDICATES

PREDICATE_ARITY = {
    **{p: 1 for p in UNARY_PREDICATES},
    **{p: 2 for p in BINARY_PREDICATES}
}


@dataclass(frozen=True)
class Constant:
    name: str

    @property
    def is_variable(self) -> bool:
        return False

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Constant({self.name})"


@dataclass(frozen=True)
class Variable:
    name: str

    @property
    def is_variable(self) -> bool:
        return True

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Variable({self.name})"


Term = Union[Constant, Variable]


@dataclass(frozen=True)
class Atom:
    predicate: str
    terms: Tuple[Term, ...]

    def __post_init__(self):
        # Validate predicate
        if self.predicate not in ALL_PREDICATES:
            raise ValueError(f"Unknown predicate '{self.predicate}'. Allowed: {sorted(ALL_PREDICATES)}")
        expected_arity = PREDICATE_ARITY[self.predicate]
        if len(self.terms) != expected_arity:
            raise ValueError(
                f"Predicate '{self.predicate}' expects arity {expected_arity}, got {len(self.terms)}"
            )

    def is_ground(self) -> bool:
        return all(isinstance(t, Constant) for t in self.terms)

    def variables(self) -> Set[Variable]:
        return {t for t in self.terms if isinstance(t, Variable)}

    def constants(self) -> Set[Constant]:
        return {t for t in self.terms if isinstance(t, Constant)}

    def __str__(self) -> str:
        args_str = ", ".join(str(t) for t in self.terms)
        return f"{self.predicate}({args_str})"

    def __repr__(self) -> str:
        return f"Atom({self.predicate}, {self.terms})"


@dataclass
class Rule:
    head: Atom
    body: List[Atom]
    name: str = ""
    rule_id: Optional[int] = None

    def __post_init__(self):
        head_vars = self.head.variables()
        body_vars = self.body_variables()
        unbound = head_vars - body_vars
        if unbound:
            unbound_names = ", ".join(v.name for v in unbound)
            raise ValueError(
                f"Safety condition violated: head variable(s) {{{unbound_names}}} not present in rule body"
            )

    def body_variables(self) -> Set[Variable]:
        res = set()
        for a in self.body:
            res.update(a.variables())
        return res

    def all_variables(self) -> Set[Variable]:
        return self.head.variables() | self.body_variables()

    def standardize_apart(self, suffix: Union[str, int]) -> 'Rule':
        """Rename all variables by appending suffix to avoid variable name collision in SLD."""
        var_map = {v: Variable(f"{v.name}_{suffix}") for v in self.all_variables()}

        def rename_atom(atom: Atom) -> Atom:
            new_terms = tuple(var_map.get(t, t) for t in atom.terms)
            return Atom(atom.predicate, new_terms)

        new_head = rename_atom(self.head)
        new_body = [rename_atom(a) for a in self.body]
        return Rule(head=new_head, body=new_body, name=self.name, rule_id=self.rule_id)

    def to_fol_unicode(self) -> str:
        vars_ordered = sorted(list(self.all_variables()), key=lambda v: v.name)
        quantifiers = " ".join(f"∀{v.name}" for v in vars_ordered)
        body_str = " ∧ ".join(str(a) for a in self.body)
        if quantifiers:
            return f"{quantifiers} ({body_str} → {self.head})"
        return f"{body_str} → {self.head}"

    def __str__(self) -> str:
        body_str = " ∧ ".join(str(a) for a in self.body)
        return f"{body_str} → {self.head}"

    def __repr__(self) -> str:
        return f"Rule(head={self.head}, body={self.body}, name={self.name}, id={self.rule_id})"
