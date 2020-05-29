from cqapk_to_datalog.data_structures import AtomValue, Atom, ConjunctiveQuery, FunctionalDependency, FunctionalDependencySet
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
    fd0 = FunctionalDependencySet()
    fd0.add(FunctionalDependency(frozenset([x]), y))
    fd1 = FunctionalDependencySet()
    fd1.add(FunctionalDependency(frozenset([x]), z))
    fd2 = FunctionalDependencySet()
    fd2.add(FunctionalDependency(frozenset([x]), z))
    q = ConjunctiveQuery({
        r: (fd0, [True, False], False),
        s: (fd1, [True, False], False),
        t: (fd2, [True, False], False)
    }, [])
    bad = find_bad_internal_fd(q)
    assert len(bad) > 0
    q, rules = saturate(q, bad)
    bad = find_bad_internal_fd(q)
    assert len(bad) == 0


