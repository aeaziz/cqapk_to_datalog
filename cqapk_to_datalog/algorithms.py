import networkx as nx
from typing import Set, List, FrozenSet, Dict
from cqapk_to_datalog.data_structures import AtomValue, Atom, FunctionalDependency, ConjunctiveQuery, SequentialProof
from copy import deepcopy


def generate_renaming(n: int, variables: List[AtomValue]) -> List[Dict[AtomValue, AtomValue]]:
    """
    Generate n renaming for a given list of variables
    :param n:           Number of renaming
    :param variables:   list of variables
    :return:            A list of dictionaries that maps each variable to their renamed variable
    """

    renaming_list = []
    for i in range(n):
        renaming = {}
        for var in variables:
            renaming[var] = AtomValue(var.name + "_" + str(i), True)
        renaming_list.append(renaming)
    return renaming_list


def apply_renaming_to_atom_values(atom_values: List[AtomValue], renaming: Dict[AtomValue, AtomValue]):
    """
    Applies a given valuation to a given list of variables
    :param atom_values:     List of variables
    :param renaming:        A Dict representing a renaming
    :return                 List of variables such that each element is the result of applying valuation over an
                            element of atom_values
    """
    res = []
    for av in atom_values:
        if av.var and av in renaming:
            res.append(renaming[av])
        else:
            res.append(av)
    return res


def apply_renaming_to_atom(atom: Atom, renaming: Dict[AtomValue, AtomValue]) -> Atom:
    """
    Applies a given valuation over a given Atom
    :param atom:            An Atom
    :param renaming:        A Dict representing a renaming
    :return:                A new Atom (same name as atom) such that its content is the application of valuation over
                            the content of atom
    """
    return Atom(atom.name, apply_renaming_to_atom_values(atom.content, renaming))


def is_self_join_free(q: ConjunctiveQuery) -> bool:
    atoms = list(q.get_atoms())
    for i in range(len(atoms)):
        atom = atoms[i]
        for other in atoms[:i] + atoms[i + 1:]:
            if atom.name == other.name:
                return False
    return True


def transitive_closure(var: Set[AtomValue], fd_set: FrozenSet[FunctionalDependency]) -> Set[AtomValue]:
    """
    Computes the transitive closure of a set of variables given a set of FD
    :param var:         Set of variables
    :param fd_set:      Set of FD
    :return:            The transitive closure of var using fd_set
    """
    closure = var.copy()
    size = 0
    while len(closure) != size:
        size = len(closure)
        for fd in fd_set:
            if all(v in closure for v in fd.left) and fd.right not in closure:
                closure.add(fd.right)
    return closure


def atom_plus(atom: Atom, q: ConjunctiveQuery) -> Set[AtomValue]:
    """
    Computes the plus q set of an atom (Read articles for more information)
    :param atom:        Atom whose plus will be computed
    :param q:           A ConjunctiveQuery
    :return:            The plus q set of variables of atom
    """
    if q.is_atom_consistent(atom):
        return transitive_closure(set(q.get_key_vars(atom)), q.get_all_fd())
    else:
        return transitive_closure(set(q.get_key_vars(atom)), q.get_all_fd(atom))


def gen_attack_graph(q: ConjunctiveQuery) -> nx.DiGraph:
    """
    Computes the attack graph of a given ConjunctiveQuery q. It computes first direct links a -> b and then uses
    b to find nodes c such as a -> c
    :param q:   A ConjunctiveQuery
    :return:    Generated Attack Graph
    """
    g = nx.DiGraph()
    atoms = q.get_atoms()
    for atom in atoms:
        g.add_node(atom)
    for atom in atoms:
        variables = set(atom.variables())
        attacked = []
        plus = atom_plus(atom, q)
        for other in [o for o in atoms if atom != o]:
            other_variables = set(other.variables())
            inter = variables.intersection(other_variables)
            inter = inter - set(plus)
            if inter:
                attacked.append(other)

        size = 0
        current = attacked
        while size != len(attacked):
            size = len(attacked)
            news = []
            for intermediate in current:
                for other in [o for o in atoms if o not in attacked and o != atom]:
                    inter = set(intermediate.variables()).intersection(set(other.variables()))
                    inter = inter - set(plus)
                    if inter:
                        attacked.append(other)
                        news.append(other)
            current = news

        for other in attacked:
            g.add_edge(atom, other)
    return g


def gen_m_graph(q: ConjunctiveQuery) -> nx.DiGraph:
    """
    Generates a M Graph
    :param q:   A ConjunctiveQuery
    :return:    M Graph generated from atoms
    """
    atoms = q.get_atoms()
    g = nx.DiGraph()
    for atom1 in atoms:
        g.add_node(atom1)
        closure = transitive_closure(set(atom1.variables()), q.get_consistent_fd())
        for atom2 in [atom for atom in atoms if atom != atom1]:
            if set(q.get_key_vars(atom2)).issubset(closure):
                g.add_edge(atom1, atom2)
    return g


def all_cycles_weak(attack_graph: nx.DiGraph, q: ConjunctiveQuery) -> bool:
    """
    Returns True if the given Attack Graph contains no strong cycle
    :param attack_graph:    An Attack Graph
    :param q:               A ConjunctiveQuery
    :return:                True if attack_graph contains no strong cycle, False if not
    """
    cycles = nx.algorithms.simple_cycles(attack_graph)
    for cycle in cycles:
        full_cycle = cycle + [cycle[0]]
        for i in range(0, len(cycle)):
            atom1 = full_cycle[i]
            atom2 = full_cycle[i + 1]
            for var in q.get_key_vars(atom2):
                if var not in transitive_closure(set(q.get_key_vars(atom1)), q.get_all_fd()):
                    return False
    return True


def atom_attacks_variables(atom: Atom, var: AtomValue, q: ConjunctiveQuery) -> bool:
    """
    Returns True if the given atom attacks the given Variable
    :param atom:        An Atom
    :param var:         A Variable
    :param q:           A ConjunctiveQuery
    :return:            True if atom attacks var, else returns False
    """
    n = Atom("N", [var])
    q_new = deepcopy(q)
    q_new.content[n] = (frozenset(), [True], False)
    g = gen_attack_graph(q_new)
    return g.has_edge(atom, n)


def sequential_proofs(fd: FunctionalDependency, q: ConjunctiveQuery) -> List[SequentialProof]:
    """
    Returns all the sequential proofs for a given FD
    :param fd :     A FD
    :param q:       A ConjunctiveQuery
    :return:        A SequentialProof object for fd
    """
    res = []
    sequential_proof_rec(fd, fd.left, q, [], res)
    return res


def sequential_proof_rec(fd: FunctionalDependency, acc: Set[AtomValue], q: ConjunctiveQuery, current_sp: List[Atom],
                         current_res: List[SequentialProof]) -> None:
    """
    Recursive function used to compute sequential proofs
    :param fd:              A FD
    :param acc:             A set of Variables containing the variables implied by the current sequential proof
    :param q:               A ConjunctiveQuery
    :param current_sp:      Current sequential proof
    :param current_res:     List that will contain all the sequential proofs
    """
    if fd.right in acc:
        sequential_proof = SequentialProof(fd, current_sp)
        to_remove = []
        for sp in current_res:
            if sequential_proof.is_subset_of(sp):
                to_remove.append(sp)
            elif sp.is_subset_of(sequential_proof):
                return None
        for sp in to_remove:
            current_res.remove(sp)
        current_res.append(sequential_proof)
    else:
        for atom in [atom for atom in q.get_atoms() if atom not in current_sp]:
            if set(q.get_key_vars(atom)).issubset(acc):
                sequential_proof_rec(fd, acc.union(set(atom.variables())), q, current_sp + [atom],
                                     current_res)


def fd_is_internal(fd: FunctionalDependency, q: ConjunctiveQuery) -> bool:
    """
    Checks if a FD is internal
    :param fd:      A FD
    :param q:       A ConjunctiveQuery
    :return:        True if fd is internal
    """
    in_atom = False
    atoms = q.get_atoms()
    for atom in atoms:
        if fd.left.issubset(set(atom.variables())):
            in_atom = True
    if not in_atom:
        return False
    sps = sequential_proofs(fd, q)
    variables = fd.left.union({fd.right})
    for sp in sps:
        valid = True
        for atom in sp.steps:
            for var in variables:
                if atom_attacks_variables(atom, var, q):
                    valid = False
        if valid:
            return True
    return False


def find_bad_internal_fd(q: ConjunctiveQuery) -> FrozenSet[FunctionalDependency]:
    """
    Given a non saturated ConjunctiveQuery, returns the FunctionalDependencies culprit of  the non saturation of the
    query.
    :param q:       A ConjunctiveQuery.
    :return:        A FrozenSet of FunctionalDependency culprit of  the non saturation of q.
    """
    res = frozenset()
    possible_starts = []
    possible_ends = []
    for fd in q.get_all_fd():
        if fd.left not in possible_starts:
            possible_starts.append(fd.left)
        if fd.right not in possible_ends:
            possible_ends.append(fd.right)
    for left in possible_starts:
        for right in possible_ends:
            test_fd = FunctionalDependency(left, right)
            if fd_is_internal(test_fd, q):
                if right not in transitive_closure(set(left), q.get_consistent_fd()):
                    res = res.union(frozenset([test_fd]))
    return res


def initial_strong_components(graph: nx.DiGraph) -> List[Set[Atom]]:
    """
    Returns the Initial Strong Components of a given Graph
    :param graph:   A Graph.
    :return:        The Initial Strong Components of graph.
    """
    iscc = []
    sccs = nx.strongly_connected_components(graph)
    for scc in sccs:
        atoms = set(scc)
        predecessors_set = set()
        for atom in atoms:
            predecessors_set = predecessors_set.union(set(graph.predecessors(atom)))
        if predecessors_set.issubset(atoms):
            iscc.append(atoms)
    return iscc
