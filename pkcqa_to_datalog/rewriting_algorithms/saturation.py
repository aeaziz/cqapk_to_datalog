from pkcqa_to_datalog.data_structures import ConjunctiveQuery, FunctionalDependency, Atom, AtomValue, EqualityAtom, DatalogQuery
from pkcqa_to_datalog.algorithms import generate_renaming, apply_renaming_to_atom_values, apply_renaming_to_atom
from typing import FrozenSet, List, Tuple

"""
This module is used to handle the saturation of a non saturated query.
"""


def saturate(q: ConjunctiveQuery, bad_fd: FrozenSet[FunctionalDependency]) -> Tuple[DatalogQuery, List[DatalogQuery]]:
    """
    Saturates a non saturated query.
    :param q:           A non saturated ConjunctiveQuery.
    :param bad_fd:      Set of internal FD that makes q non saturated
    :return:            A set of Datalog rules. q is also modified.
    """
    n_index = 0
    atoms = q.get_atoms()
    output = []
    for fd in bad_fd:
        content = list(fd.left) + [fd.right]
        n_atom = Atom("N_" + str(n_index), content)
        new_q = q.add_atom(n_atom, frozenset([fd]), [True] * len(fd.left) + [False], True)
        valuation = generate_renaming(1, list(new_q.get_all_variables()))[0]
        n_rule = DatalogQuery(n_atom)
        for atom in atoms:
            n_rule.add_atom(atom)
        bad_atom = Atom("BadFact_" + str(n_index), content)
        n_rule.add_atom(bad_atom, True)
        bad_rule = DatalogQuery(bad_atom)
        for atom in atoms:
            bad_rule.add_atom(atom)
            bad_rule.add_atom(apply_renaming_to_atom(atom, valuation))
        for var in fd.left:
            bad_rule.add_atom(EqualityAtom(var, valuation[var]))
        bad_rule.add_atom(EqualityAtom(fd.right, valuation[fd.right], True))
        output += [n_rule, bad_rule]
    return new_q, output
