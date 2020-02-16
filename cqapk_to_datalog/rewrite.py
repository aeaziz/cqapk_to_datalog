import traceback
import networkx as nx
from typing import List
from cqapk_to_datalog.data_structures import ConjunctiveQuery, DatalogQuery
from cqapk_to_datalog.algorithms import gen_attack_graph, gen_m_graph, all_cycles_weak, find_bad_internal_fd, initial_strong_components\
    , is_self_join_free
from cqapk_to_datalog.rewriting_algorithms.fo_rewriting import rewrite_fo
from cqapk_to_datalog.rewriting_algorithms.cycle_reduce import reduce_cycle
from cqapk_to_datalog.rewriting_algorithms.saturation import saturate

'''
This module contains the main rewriting algorithm.
'''


def rewrite(q: ConjunctiveQuery) -> List[DatalogQuery]:
    """
    Main rewriting algorithm.
    Described in README File.
    :param q:   A ConjunctiveQuery.
    :return:    A List of DatalogQueries representing a Datalog program which is the rewriting of CERTAINTY(q).
    """
    if not is_self_join_free(q):
        raise CustomException("The Conjunctive Query given as input is not self-join free.")
    saturation_rules = []
    reduction_rules = []
    rewriting_rules = []
    a_graph = gen_attack_graph(q)
    if all_cycles_weak(a_graph, q):
        bad = find_bad_internal_fd(q)
        if len(bad) != 0:
            saturation_rules += saturate(q, bad)
        a_cycles = list(nx.algorithms.simple_cycles(a_graph))
        reduction_index = 0
        while len(a_cycles) > 0:
            m_graph = gen_m_graph(q)
            m_cycles = nx.simple_cycles(m_graph)
            isccs = initial_strong_components(a_graph)
            good_cycles = []
            for cycle in m_cycles:
                for iscc in isccs:
                    if set(cycle).issubset(iscc):
                        good_cycles.append(cycle)
            q, rules = reduce_cycle(good_cycles[0], q, reduction_index)
            reduction_rules += rules
            a_graph = gen_attack_graph(q)
            a_cycles = list(nx.algorithms.simple_cycles(a_graph))
            reduction_index += 1
        topological_sort = list(nx.topological_sort(a_graph))
        rewriting_rules += rewrite_fo(q, topological_sort)
        return saturation_rules + reduction_rules + rewriting_rules
    else:
        raise CustomException("The rewriting of the given query is a NP-Hard problem...")


class CustomException(Exception):
    """
    Exception used to handle NP-Hard Queries
    """

    def __init__(self, msg):
        self.msg = msg
