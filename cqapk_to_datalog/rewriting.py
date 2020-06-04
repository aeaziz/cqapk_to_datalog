import cqapk_to_datalog.algorithms as algorithms
import cqapk_to_datalog.data_structures as structures
import cqapk_to_datalog.rules_templates as templates
from typing import List, Tuple, FrozenSet, Set, Dict
from cqapk_to_datalog.exceptions import NotSelfJoinFreeQuery, CoNPComplete


def rewrite(q: structures.ConjunctiveQuery) -> structures.DatalogProgram:
    """
    Main rewriting algorithm.
    :param q:   A ConjunctiveQuery.
    :return:    A List of DatalogQueries representing a Datalog program which is the rewriting of CERTAINTY(q).
    """
    if not algorithms.is_self_join_free(q):
        raise NotSelfJoinFreeQuery
    output_rules = []
    done = set()
    fo_index = 0
    reduction_index = 0
    current_q = q
    a_graph = algorithms.gen_attack_graph(current_q)
    if algorithms.all_cycles_weak(a_graph, current_q):
        while len(a_graph.nodes) > 0:
            not_attacked_atoms = [atom for atom in current_q.get_atoms() if a_graph.in_degree(atom) == 0]
            if len(not_attacked_atoms) > 0:
                atom = not_attacked_atoms[0]
                current_q, new_rules = rewrite_fo(current_q, atom, len(a_graph.nodes) == 1, done, fo_index)
                done.add(atom)
                fo_index += 1
                output_rules += new_rules
            else:
                bad = algorithms.find_bad_internal_fd(current_q)
                if len(bad) != 0:
                    current_q, saturation_rules = saturate(current_q, bad)
                    output_rules += saturation_rules
                reducible_cycle = algorithms.get_reductible_sets(current_q, a_graph)[0]
                current_q, new_rules = reduce_cycle(reducible_cycle, current_q, reduction_index)
                reduction_index += 1
                output_rules += new_rules
            a_graph = algorithms.gen_attack_graph(current_q)
        return structures.DatalogProgram(output_rules)
    else:
        raise CoNPComplete


def rewrite_fo(q: structures.ConjunctiveQuery, atom: structures.Atom, is_last: bool, done: Set[structures.Atom],
               index) -> Tuple[structures.ConjunctiveQuery, List[structures.DatalogQuery]]:
    """
    Rewrites CERTAINTY(q) in function of a given atom when CERTAINTY(q) is in FO.
    :param q:                       A sjfBCQ
    :param atom:					Atom being rewrited
    :param is_last:					True if q\{atom} has already been treated
    :param done:                    A set of the Atom that have already been treated by the rewriting process
    :param index:                   Index used to enumerate the Datalog rules
    :return:                        A list of Datalog rules and a ConjunctiveQuery that corresponds to q\{atom} where
                                    the variables in atoms are constants.
    """
    rules = []
    data = templates.RewritingData(q, atom, index, is_last, done)
    rules.append(templates.RewriteAtomQuery(data))
    if data.has_c or not data.is_last:
        rules.append(templates.BadBlockQuery(data))
        if data.has_c:
            rules.append(templates.GoodFactQuery(data))
    new_q = q.remove_atom(atom)
    for var in data.v:
        new_q = new_q.release_variable(var)
    return new_q, rules


def reduce_cycle(cycle: List[structures.Atom], q: structures.ConjunctiveQuery,
                 rewriting_index: int) -> Tuple[structures.ConjunctiveQuery, List[structures.DatalogQuery]]:
    """
    Reduces a cycle in the M-graph corresponding to an initial strong component in the attack graph of q.
    :param cycle:				Cycle to be reduced
    :param q: 					A ConjunctiveQuery
    :param rewriting_index: 	Index used to enumerate the Datalog rules
    :return: 					A list of Datalog rules and a ConjunctiveQuery that corresponds to
                                q\{atom} U {T} U {Nc} (Just as described in the report)
    """
    rules = []
    k = len(cycle)
    renamings = algorithms.generate_renaming(2 * k + 2, list(q.get_all_variables()))
    rules += [templates.EqQuery(atom, q) for atom in cycle]
    rules += [templates.NeqQuery(atom, q, renamings[0]) for atom in cycle]
    rules += garbage_set_rules(cycle, q, rewriting_index, renamings)
    rules += new_atoms_rules(cycle, q, rewriting_index, renamings)
    t, n_atoms = new_atoms(cycle, q, rewriting_index, renamings[0])
    new_q = q.add_atom(*t)
    for n_atom in n_atoms:
        new_q = new_q.add_atom(*n_atom)
    for atom in cycle:
        new_q = new_q.remove_atom(atom)
    return new_q, rules


def garbage_set_rules(cycle: List[structures.Atom], q: structures.ConjunctiveQuery, rewriting_index: int,
                      renamings: List[Dict[structures.AtomValue, structures.AtomValue]]):
    """
    Generated the Datalog rules needed to compute the maximum garbage set of a cycle C in the M-graph of q.
    :param cycle:				A cycle in the M-graph of q
    :param q:					A ConjunctiveQuery
    :param rewriting_index: 	Index used to enumerate the Datalog rules
    :param renamings:           Necessary renamings
    :return:
    """
    rules = []
    rules += [templates.RelevantQuery(atom, q) for atom in cycle]
    rules += [templates.GarbageRelevantQuery(atom, q) for atom in cycle]
    rules += [templates.Any1EmbQuery(cycle, q, rewriting_index, renamings)]
    rules += [templates.Rel1EmbQuery(cycle, q, rewriting_index)]
    rules += [templates.Irr1EmbQuery(cycle, q, rewriting_index, renamings)]
    rules += [templates.Garbage1EmbQuery(atom, cycle, q, rewriting_index, renamings) for atom in cycle]
    rules += [templates.PkQuery(cycle, q, rewriting_index, renamings)]
    rules += [templates.DConBaseQuery(cycle, q, rewriting_index, renamings),
              templates.DConRecQuery(cycle, q, rewriting_index, renamings)]
    rules += [templates.InLongDCycleQuery(cycle, q, rewriting_index, renamings)]
    rules += [templates.GarbageLongCycleQuery(atom, cycle, q, rewriting_index) for atom in cycle]
    rules += [templates.GarbagePropagateQuery(atom1, atom2, q) for atom1 in cycle for atom2 in cycle if atom1 != atom2]
    return rules


def new_atoms(cycle: List[structures.Atom], q: structures.ConjunctiveQuery, rewriting_index: int,
              renaming: Dict[structures.AtomValue, structures.AtomValue]) -> \
        Tuple[Tuple[structures.Atom, structures.FunctionalDependencySet, List[bool], bool],
              List[Tuple[structures.Atom, structures.FunctionalDependencySet, List[bool], bool]]]:
    """
    Generates the atoms needed for the reduction
    :param cycle:				Cycle being reduced
    :param q:					A ConjunctiveQuery
    :param rewriting_index:		Index used to enumerate the Datalog rules
    :param renaming:			Necessary renaming
    :return:					Atoms needed for the reduction
    """
    _, x_0, _ = q.decompose_atom(cycle[0])
    x_0_ren = algorithms.apply_renaming_to_atom_values(x_0, renaming)
    n_atoms = []
    t_content = []
    t_released = set()
    for atom in cycle:
        _, x, y = q.decompose_atom(atom)
        n = structures.Atom("N_" + atom.name, x + x_0_ren, atom.released)
        t_released = t_released.union(atom.released)
        fd = structures.FunctionalDependencySet()
        for var in x_0_ren:
            fd.add(structures.FunctionalDependency(x, var))
        is_key = [True] * len(x) + [False] * len(x_0_ren)
        n_atoms.append((n, fd, is_key, True))
        t_content += x
        t_content += y
    t = structures.Atom("T_" + str(rewriting_index), x_0_ren + t_content, t_released)
    fd = structures.FunctionalDependencySet()
    for var in t_content:
        fd.add(structures.FunctionalDependency(x_0_ren, var))
    is_key = [True] * len(x_0_ren) + [False] * len(t_content)
    return (t, fd, is_key, False), n_atoms


def new_atoms_rules(cycle: List[structures.Atom], q: structures.ConjunctiveQuery, rewriting_index : int,
                    renamings: List[Dict[structures.AtomValue, structures.AtomValue]]) -> List[structures.DatalogQuery]:
    """
    Generated the rules defining the new atoms added by the reduction
    :param cycle: 				Cycle being reduced
    :param q: 					A ConjunctiveQuery
    :param rewriting_index: 	Index used to enumerate the Datalog rules
    :param renamings: 			Necessary renamings
    :return: 					Rules defining the new atoms
    """
    _, x_0, _ = q.decompose_atom(cycle[0])
    rules = []
    rules += [templates.KeepQuery(atom, q) for atom in cycle]
    rules += [templates.LinkQuery(atom, cycle, q, rewriting_index, renamings[0]) for atom in cycle]
    rules += [templates.TransBaseQuery(cycle, q, rewriting_index, renamings[0])]
    rules += [templates.TransRecQuery(cycle, q, rewriting_index, renamings)]
    if len(x_0) > 1:
        rules += [templates.LowerCompositeQuery(cycle, q, i, rewriting_index, renamings) for i in range(len(cycle))]
    else:
        rules += [templates.LowerSingleQuery(cycle, q, rewriting_index, renamings)]
    rules += [templates.IdentifiedByQuery(cycle, q, rewriting_index, renamings[0])]
    rules += [templates.NQuery(atom, cycle, q, rewriting_index, renamings[0]) for atom in cycle]
    rules += [templates.TQuery(cycle, q, rewriting_index, renamings[0])]
    return rules


def saturate(q: structures.ConjunctiveQuery, bad_fd: FrozenSet[structures.FunctionalDependency]) \
        -> Tuple[structures.ConjunctiveQuery, List[structures.DatalogQuery]]:
    """
    Saturates a non saturated query.
    :param q:           A non saturated ConjunctiveQuery.
    :param bad_fd:      Set of internal FD that makes q non saturated
    :return:            The saturated query and a set of Datalog rules.
    """
    n_index = 0
    atoms = q.get_atoms()
    output = []
    new_q = q
    for fd in bad_fd:
        content = list(fd.left) + [fd.right]
        n_atom = structures.Atom("N_" + str(n_index), content)
        fd_set = structures.FunctionalDependencySet()
        fd_set.add(fd)
        new_q = q.add_atom(n_atom, fd_set, [True] * len(fd.left) + [False], True)
        valuation = algorithms.generate_renaming(1, list(new_q.get_all_variables()))[0]
        n_rule = structures.DatalogQuery(n_atom)
        for atom in atoms:
            n_rule.add_atom(atom)
        bad_atom = structures.Atom("BadFact_" + str(n_index), content)
        n_rule.add_atom(bad_atom, True)
        bad_rule = structures.DatalogQuery(bad_atom)
        for atom in atoms:
            bad_rule.add_atom(atom)
            bad_rule.add_atom(algorithms.apply_renaming_to_atom(atom, valuation))
        for var in fd.left:
            bad_rule.add_atom(structures.EqualityAtom(var, valuation[var]))
        bad_rule.add_atom(structures.EqualityAtom(fd.right, valuation[fd.right], True))
        output += [n_rule, bad_rule]
    return new_q, output
