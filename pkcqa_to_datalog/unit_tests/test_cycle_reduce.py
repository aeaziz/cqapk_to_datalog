from pkcqa_to_datalog.data_structures import AtomValue, Atom, DatalogQuery, ConjunctiveQuery, FunctionalDependency
from pkcqa_to_datalog.rewriting_algorithms.cycle_reduce import reduce_cycle
from pkcqa_to_datalog.rewriting_algorithms.fo_rewriting import rewrite_fo
from pkcqa_to_datalog.algorithms import gen_attack_graph
import networkx as nx


def test_pk_query():
    # TODO
    x = AtomValue("X", True)
    y = AtomValue("Y", True)
    z = AtomValue("Z", True)
    r = Atom("R", [x, y])
    s = Atom("S", [y, z])
    t = Atom("T", [z, x])
    q = ConjunctiveQuery({
        r: (frozenset([FunctionalDependency(frozenset([x]), y)]), [True, False], False),
        s: (frozenset([FunctionalDependency(frozenset([y]), z)]), [True, False], False),
        t: (frozenset([FunctionalDependency(frozenset([z]), x)]), [True, False], False)
    }, [])
    q, rules = reduce_cycle([r, s, t], q, 0)
    atoms = []
    a_graph = gen_attack_graph(q)
    rules += rewrite_fo(q, list(nx.topological_sort(a_graph)))
    #print(rules)
