from cqapk_to_datalog.data_structures import AtomValue, Atom, ConjunctiveQuery, FunctionalDependency
from cqapk_to_datalog.algorithms import find_bad_internal_fd
from cqapk_to_datalog.rewriting_algorithms.saturation import saturate


def test_saturation():
    # TODO
    x = AtomValue("X", True)
    y = AtomValue("Y", True)
    z = AtomValue("Z", True)
    r = Atom("R", [x, y])
    s = Atom("S", [x, z])
    t = Atom("T", [x, z])
    q = ConjunctiveQuery({
        r: (frozenset([FunctionalDependency(frozenset([x]), y)]), [True, False], False),
        s: (frozenset([FunctionalDependency(frozenset([x]), z)]), [True, False], False),
        t: (frozenset([FunctionalDependency(frozenset([x]), z)]), [True, False], False)
    }, [])
    bad = find_bad_internal_fd(q)
    assert len(bad) > 0
    q, rules = saturate(q, bad)
    bad = find_bad_internal_fd(q)
    assert len(bad) == 0


