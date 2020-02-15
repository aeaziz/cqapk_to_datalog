from pkcqa_to_datalog.data_structures import AtomValue, Atom, ConjunctiveQuery, FunctionalDependency



def test_simple():
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