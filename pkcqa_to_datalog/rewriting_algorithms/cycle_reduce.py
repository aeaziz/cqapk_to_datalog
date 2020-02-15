from pkcqa_to_datalog.data_structures import Atom, ConjunctiveQuery, AtomValue, DatalogQuery, EqualityAtom, CompareAtom, \
    FunctionalDependency
from pkcqa_to_datalog.algorithms import generate_renaming, apply_renaming_to_atom, apply_renaming_to_atom_values
from typing import List, Tuple

'''
This module is used to reduce CERTAINITY(q) when CERTAINITY(q) is in L.
Functions are named after the Datalog rules they produce or the step in the reduction that they handle.
'''


def reduce_cycle(cycle: List[Atom], q: ConjunctiveQuery,
                 rewriting_index: int) -> Tuple[ConjunctiveQuery, List[DatalogQuery]]:
    queries = eq_queries(cycle, q)
    queries += condition3a(cycle, q)
    queries += condition3b(cycle, q, rewriting_index)
    queries += condition3c(cycle, q, rewriting_index)
    queries += condition3d(cycle, q)
    new_q, last = finish_reduction(cycle, q, rewriting_index)
    return new_q, queries + last


def get_cycle_vars(cycle: List[Atom]) -> List[AtomValue]:
    all_vars = []
    for atom in cycle:
        for var in atom.variables():
            if var not in all_vars:
                all_vars.append(var)
    return all_vars


def condition3a(cycle: List[Atom], q: ConjunctiveQuery) -> List[DatalogQuery]:
    rules = []
    for atom in cycle:
        relevant = DatalogQuery(Atom("Rlvant_" + atom.name, atom.content))
        for all_atom in cycle:
            relevant.add_atom(all_atom)
        rules.append(relevant)
        garbage = DatalogQuery(Atom("Garbage_" + atom.name, q.get_key_vars(atom)))
        garbage.add_atom(atom)
        garbage.add_atom(Atom("Rlvant_" + atom.name, atom.content), True)
        rules.append(garbage)
    return rules


def condition3b(cycle: List[Atom], q: ConjunctiveQuery, rewriting_index: int) -> List[DatalogQuery]:
    rules = []
    k = len(cycle)
    valuations = generate_renaming(k, get_cycle_vars(cycle))
    any_head_content = []
    rel_head_content = []
    irr_head_content = []
    for i in range(0, k):
        for atom in cycle:
            any_head_content += apply_renaming_to_atom_values(atom.variables(), valuations[i])
            rel_head_content += atom.variables()
            irr_head_content += apply_renaming_to_atom_values(q.get_key_vars(atom), valuations[i])
    any1emb = DatalogQuery(Atom("Any1Emb_" + str(rewriting_index), any_head_content))
    for i in range(0, k):
        for atom in cycle:
            any1emb.add_atom(apply_renaming_to_atom(atom, valuations[i]))

    for atom in cycle:
        for i in range(0, k):
            key_vars = q.get_key_vars(atom)
            eq = Atom("Eq_" + atom.name,
                      apply_renaming_to_atom_values(key_vars, valuations[(k + i) % k])
                      + apply_renaming_to_atom_values(key_vars, valuations[(k - 1 + i) % k])
                      )
            any1emb.add_atom(eq)

    rel1emb = DatalogQuery(Atom("Rel1Emb_" + str(rewriting_index), rel_head_content))
    for atom in cycle:
        rel1emb.add_atom(atom)

    irr1emb = DatalogQuery(Atom("Irr1Emb_" + str(rewriting_index), irr_head_content))
    irr1emb.add_atom(Atom("Any1Emb", any_head_content))
    irr1emb.add_atom(Atom("Rel1Emb", any_head_content), True)

    rules += [any1emb, rel1emb, irr1emb]

    for i in range(len(cycle)):
        atom = cycle[i]
        garbage = DatalogQuery(Atom("Garbage_" + atom.name,
                                    apply_renaming_to_atom_values(q.get_key_vars(atom), valuations[i])))
        garbage.add_atom(Atom("Irr1Emb", irr_head_content))
        rules.append(garbage)
    return rules


def condition3c(cycle: List[Atom], q: ConjunctiveQuery, rewriting_index: int) -> List[DatalogQuery]:
    rules = [pk_query(cycle, q, rewriting_index)]
    rules += dcon_queries(cycle, q, rewriting_index)
    rules.append(inLongDCycle_query(cycle, q, rewriting_index))
    rules += cycle_garbage_queries(cycle, q)
    return rules


def condition3d(cycle: List[Atom], q: ConjunctiveQuery) -> List[DatalogQuery]:
    queries = []
    for atom in cycle:
        for other in cycle:
            if atom != other:
                query = DatalogQuery(Atom("Garbage_" + atom.name, q.get_key_vars(atom)))
                for a in cycle:
                    query.add_atom(a)
                query.add_atom(Atom("Garbage_" + other.name, q.get_key_vars(other)))
                queries.append(query)
    return queries


def finish_reduction(cycle: List[Atom], q: ConjunctiveQuery,
                     rewriting_index: int) -> Tuple[ConjunctiveQuery, List[DatalogQuery]]:
    rules = []
    rules += keep_queries(cycle, q)
    rules += link_queries(cycle, q, rewriting_index)
    rules += trans_queries(cycle, q, rewriting_index)
    if len(q.get_key_vars(cycle[0])) > 1:
        rules += composite_id_queries(cycle, q, rewriting_index)
    else:
        rules += single_id_queries(cycle, q, rewriting_index)

    variables = get_cycle_vars(cycle)
    valuation = generate_renaming(1, variables)[0]
    key0_vars = q.get_key_vars(cycle[0])
    valuated = apply_renaming_to_atom_values(key0_vars, valuation)
    t_atom = Atom("T_" + str(rewriting_index), valuated + variables)
    t_query = DatalogQuery(t_atom)
    t_query.add_atom(Atom("IdentifiedBy" + str(rewriting_index), key0_vars + valuated))
    new_q = q
    for atom in cycle:
        t_query.add_atom(Atom("Keep_" + atom.name, atom.variables()))
        atom_key_vars = q.get_key_vars(atom)
        n_atom = Atom("N_" + atom.name, atom_key_vars + valuated)
        n_query = DatalogQuery(n_atom)
        n_query.add_atom(Atom("T_" + str(rewriting_index), valuated + variables))
        rules.append(n_query)
        fds = []
        for value in valuated:
            fds.append(FunctionalDependency(frozenset(atom_key_vars), value))
        new_q = new_q.add_atom(n_atom, frozenset(fds), [True] * len(atom_key_vars) + [False] * len(valuated), True)
    fds = []
    for value in variables:
        fds.append(FunctionalDependency(frozenset(valuated), value))
    new_q = new_q.add_atom(t_atom, frozenset(fds), [True] * len(valuated) + [False] * len(variables), False)
    rules.append(t_query)
    for atom in cycle:
        new_q = new_q.remove_atom(atom)
    return new_q, rules


def eq_queries(cycle: List[Atom], q: ConjunctiveQuery) -> List[DatalogQuery]:
    queries = []
    valuation = generate_renaming(1, get_cycle_vars(cycle))[0]
    for atom in cycle:
        key_vars = q.get_key_vars(atom)
        eq = DatalogQuery(Atom("Eq_" + atom.name, key_vars + key_vars))
        eq.add_atom(atom)
        neq = DatalogQuery(Atom("Neq_" + atom.name, key_vars + apply_renaming_to_atom_values(key_vars, valuation)))
        neq.add_atom(atom)
        neq.add_atom(apply_renaming_to_atom(atom, valuation))
        neq.add_atom(Atom("Eq_" + atom.name, key_vars + apply_renaming_to_atom_values(key_vars, valuation)), True)
        queries += [eq, neq]
    return queries


def pk_query(cycle: List[Atom], q: ConjunctiveQuery, rewriting_index: int) -> DatalogQuery:
    all_vars = get_cycle_vars(cycle)
    k = len(cycle)
    valuations = generate_renaming(k + 1, all_vars)
    head_content = []
    for i in range(len(cycle)):
        head_content = head_content + apply_renaming_to_atom_values(q.get_key_vars(cycle[i]), valuations[i])
    head_content = head_content + apply_renaming_to_atom_values(q.get_key_vars(cycle[0]), valuations[k])
    head = Atom("Pk_" + str(rewriting_index), head_content)
    query = DatalogQuery(head)
    for i in range(0, k + 1):
        for atom in q.get_atoms():
            query.add_atom(apply_renaming_to_atom(atom, valuations[i]))
    for i in range(1, k):
        atom = cycle[i]
        key_vars = q.get_key_vars(atom)
        query.add_atom(Atom("Eq_" + atom.name,
                            apply_renaming_to_atom_values(key_vars, valuations[i])
                            + apply_renaming_to_atom_values(key_vars, valuations[i - 1])
                            ))
    query.add_atom(Atom("Eq_" + cycle[0].name,
                        apply_renaming_to_atom_values(q.get_key_vars(cycle[0]), valuations[k])
                        + apply_renaming_to_atom_values(q.get_key_vars(cycle[0]), valuations[k - 1])
                        ))
    query.add_atom(Atom("Neq_" + cycle[0].name,
                        apply_renaming_to_atom_values(q.get_key_vars(cycle[0]), valuations[0])
                        + apply_renaming_to_atom_values(q.get_key_vars(cycle[0]), valuations[k])
                        ))
    return query


def dcon_queries(cycle: List[Atom], q: ConjunctiveQuery, rewriting_index: int) -> Tuple[DatalogQuery, DatalogQuery]:
    k = len(cycle)
    all_vars = get_cycle_vars(cycle)
    valuations = generate_renaming(2 * k + 2, all_vars)
    sp1 = valuations[0]
    sp2 = valuations[1]
    valuations = valuations[2:]

    valuation_0_0 = apply_renaming_to_atom_values(q.get_key_vars(cycle[0]), valuations[0])
    valuation_k_0 = apply_renaming_to_atom_values(q.get_key_vars(cycle[0]), valuations[k])
    sp1_0 = apply_renaming_to_atom_values(q.get_key_vars(cycle[0]), sp1)
    sp2_0 = apply_renaming_to_atom_values(q.get_key_vars(cycle[0]), sp2)
    from_1_to_k_1 = []
    from_k_1_to_2k_1 = []
    for i in range(1, k):
        from_1_to_k_1 = from_1_to_k_1 + apply_renaming_to_atom_values(q.get_key_vars(cycle[i]), valuations[i])
        from_k_1_to_2k_1 = from_k_1_to_2k_1 + apply_renaming_to_atom_values(q.get_key_vars(cycle[i]),
                                                                            valuations[k + i])

    rec_head_content = valuation_0_0 + sp1_0 + from_1_to_k_1
    base_head_content = sp1_0 + sp1_0 + from_1_to_k_1
    rec_content = valuation_0_0 + sp2_0 + from_1_to_k_1
    rec_pk_content = sp2_0 + from_k_1_to_2k_1 + sp1_0
    base_pk_content = valuation_0_0 + from_1_to_k_1 + valuation_k_0

    rec_head = Atom("DCon_" + str(rewriting_index), rec_head_content)
    rec_query = DatalogQuery(rec_head)
    rec_query.add_atom(Atom("DCon_" + str(rewriting_index), rec_content))
    rec_query.add_atom(Atom("Pk_" + str(rewriting_index), rec_pk_content))
    for i in range(1, k):
        valued_1 = apply_renaming_to_atom_values(q.get_key_vars(cycle[i]), valuations[k + i])
        valued_2 = apply_renaming_to_atom_values(q.get_key_vars(cycle[i]), valuations[i])
        rec_query.add_atom(Atom("Neq_" + cycle[i].name, valued_1 + valued_2))

    base_head = Atom("DCon_" + str(rewriting_index), base_head_content)
    base_query = DatalogQuery(base_head)
    for atom in q.get_atoms():
        base_query.add_atom(apply_renaming_to_atom(atom, sp1))
    base_query.add_atom(Atom("Pk_" + str(rewriting_index), base_pk_content))

    return rec_query, base_query


def inLongDCycle_query(cycle: List[Atom], q: ConjunctiveQuery, rewriting_index: int) -> DatalogQuery:
    k = len(cycle)
    all_vars = get_cycle_vars(cycle)
    valuations = generate_renaming(k + 1, all_vars)
    valuation_k_0 = apply_renaming_to_atom_values(q.get_key_vars(cycle[0]), valuations[k])
    from_0_to_k_1 = []
    for i in range(0, k):
        from_0_to_k_1 = from_0_to_k_1 + apply_renaming_to_atom_values(q.get_key_vars(cycle[i]), valuations[i])

    query = DatalogQuery(Atom("InLongDCycle_" + str(rewriting_index), from_0_to_k_1))
    pk_content = from_0_to_k_1 + valuation_k_0
    dcon_content = valuation_k_0 + from_0_to_k_1
    query.add_atom(Atom("Pk_" + str(rewriting_index), pk_content))
    query.add_atom(Atom("DCon_" + str(rewriting_index), dcon_content))

    return query


def cycle_garbage_queries(cycle: List[Atom], q: ConjunctiveQuery) -> List[DatalogQuery]:
    queries = []
    for atom in cycle:
        query = DatalogQuery(Atom("Garbage_" + atom.name, q.get_key_vars(atom)))
        query.add_atom(Atom("InLongDCycle", get_cycle_vars(cycle)))
        queries.append(query)
    return queries


def keep_queries(cycle: List[Atom], q: ConjunctiveQuery) -> List[DatalogQuery]:
    queries = []
    for atom in cycle:
        query = DatalogQuery(Atom("Keep_" + atom.name, atom.variables()))
        query.add_atom(atom)
        query.add_atom(Atom("Garbage_" + atom.name, q.get_key_vars(atom)), True)
        queries.append(query)
    return queries


def link_queries(cycle: List[Atom], q: ConjunctiveQuery, rewriting_index: int) -> List[DatalogQuery]:
    queries = []
    k = len(cycle)
    valuation = generate_renaming(1, get_cycle_vars(cycle))[0]
    head_content = q.get_key_vars(cycle[0]) + apply_renaming_to_atom_values(q.get_key_vars(cycle[0]), valuation)
    head = Atom("Link_" + str(rewriting_index), head_content)
    for i in range(0, k):
        query = DatalogQuery(head)
        for atom in cycle:
            query.add_atom(Atom("Keep_" + atom.name, atom.variables()))
            query.add_atom(Atom("Keep_" + atom.name, apply_renaming_to_atom_values(atom.variables(), valuation)))
        keys = q.get_key_vars(cycle[i])
        query.add_atom(Atom("Eq_" + cycle[i].name, keys + apply_renaming_to_atom_values(keys, valuation)))
        queries.append(query)
    return queries


def trans_queries(cycle: List[Atom], q: ConjunctiveQuery, rewriting_index: int) \
        -> Tuple[DatalogQuery, DatalogQuery, DatalogQuery]:
    valuations = generate_renaming(2, get_cycle_vars(cycle))
    sp1 = valuations[0]
    sp2 = valuations[1]

    x0 = q.get_key_vars(cycle[0])
    x0_sp1 = apply_renaming_to_atom_values(x0, sp1)
    x0_sp2 = apply_renaming_to_atom_values(x0, sp2)

    trans1_query = DatalogQuery(Atom("Trans_" + str(rewriting_index), x0 + x0_sp1))
    trans1_query.add_atom(Atom("Link_" + str(rewriting_index), x0 + x0_sp1))

    trans2_query = DatalogQuery(Atom("Trans_" + str(rewriting_index), x0 + x0_sp1))
    trans3_query = DatalogQuery(Atom("Trans_" + str(rewriting_index), x0 + x0_sp2))

    trans2_query.add_atom(Atom("Trans_" + str(rewriting_index), x0 + x0_sp2))
    trans2_query.add_atom(Atom("Link_" + str(rewriting_index), x0_sp2 + x0_sp1))
    trans3_query.add_atom(Atom("Trans_" + str(rewriting_index), x0 + x0_sp1))
    trans3_query.add_atom(Atom("Link_" + str(rewriting_index), x0_sp2 + x0_sp1))

    return trans1_query, trans2_query, trans3_query


def single_id_queries(cycle: List[Atom], q: ConjunctiveQuery, index: int) -> List[DatalogQuery]:
    id_vars = q.get_key_vars(cycle[0])
    valuations = generate_renaming(2, id_vars)
    valuated0 = apply_renaming_to_atom_values(id_vars, valuations[0])
    valuated1 = apply_renaming_to_atom_values(id_vars, valuations[1])
    lower = DatalogQuery(Atom("Lower_" + str(index), id_vars + valuated0))
    lower.add_atom(Atom("Trans_" + str(index), id_vars + valuated0))
    lower.add_atom(Atom("Trans_" + str(index), id_vars + valuated1))
    lower.add_atom(CompareAtom(valuations[0][id_vars[0]], valuations[1][id_vars[0]], False))

    id_query = DatalogQuery(
        Atom("IdentifiedBy" + str(index), id_vars + valuated0))
    id_query.add_atom(Atom("Lower_" + str(index), id_vars + valuated0), True)
    id_query.add_atom(Atom("Trans_" + str(index), id_vars + valuated0))
    return [lower, id_query]


def composite_id_queries(cycle: List[Atom], q: ConjunctiveQuery, index: int) -> List[DatalogQuery]:
    rules = []
    id_vars = q.get_key_vars(cycle[0])
    valuations = generate_renaming(2, id_vars)
    valuated0 = apply_renaming_to_atom_values(id_vars, valuations[0])
    valuated1 = apply_renaming_to_atom_values(id_vars, valuations[1])
    trans1 = Atom("Trans_" + str(index), id_vars + valuated0)
    trans2 = Atom("Trans_" + str(index), id_vars + valuated1)
    for i in range(len(id_vars)):
        lower = DatalogQuery(Atom("Lower_" + str(index), id_vars + valuated0))
        lower.add_atom(trans1)
        lower.add_atom(trans2)
        for j in range(i):
            lower.add_atom(EqualityAtom(valuations[0][id_vars[j]], valuations[1][id_vars[j]], False))
        lower.add_atom(CompareAtom(valuations[0][id_vars[i]], valuations[1][id_vars[i]], False))
        rules.append(lower)

    id_query = DatalogQuery(
        Atom("IdentifiedBy" + str(index), id_vars + valuated0))
    id_query.add_atom(Atom("Lower_" + str(index), id_vars + valuated0), True)
    id_query.add_atom(Atom("Trans_" + str(index), id_vars + valuated0))
    rules.append(id_query)
    return rules
