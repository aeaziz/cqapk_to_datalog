from cqapk_to_datalog.data_structures import AtomValue, Atom, EqualityAtom, CompareAtom, DatalogQuery, ConjunctiveQuery, \
    FunctionalDependency
from cqapk_to_datalog.file_handle import read_datalog_file, read_cq_file


def test_read_datalog():
    x = AtomValue("X", True)
    y = AtomValue("Y", True)
    a = AtomValue("a", False)
    b = AtomValue("b", False)
    q1 = DatalogQuery(Atom("R", [x, y]))
    q1.add_atom(Atom("S", [y, x]))
    q1.add_atom(Atom("T", [x, x]))

    q2 = DatalogQuery(Atom("R", [a, y]))
    q2.add_atom(Atom("S", [y, a]))
    q2.add_atom(Atom("T", [a, a]))

    q3 = DatalogQuery(Atom("S", [y, x]))
    q3.add_atom(Atom("R", [x, y]))
    q3.add_atom(EqualityAtom(y, b))

    q4 = DatalogQuery(Atom("T", [y, x]))
    q4.add_atom(Atom("R", [x, y]))
    q4.add_atom(EqualityAtom(y, b, True))

    q5 = DatalogQuery(Atom("V", [y, x]))
    q5.add_atom(Atom("R", [x, y]))
    q5.add_atom(CompareAtom(y, b, True))

    q6 = DatalogQuery(Atom("W_8", [y, x]))
    q6.add_atom(Atom("R", [x, y]))
    q6.add_atom(CompareAtom(y, b, False))

    queries = [q1, q2, q3, q4, q5, q6]
    read_queries = read_datalog_file("../sample_files/Datalog/test_read.txt")
    assert len(queries) == len(read_queries)
    for i in range(len(queries)):
        assert queries[i] == read_queries[i]


def test_read_cq():
    x = AtomValue("X", True)
    y = AtomValue("Y", True)
    z = AtomValue("Z", True)
    a = AtomValue("a", False)
    b = AtomValue("b", False)
    r = Atom("R", [x, a, y,z])
    s = Atom("S", [y, x, b])
    fd0 = FunctionalDependency(frozenset([x]), y)
    fd1 = FunctionalDependency(frozenset([x]), z)
    fd2 = FunctionalDependency(frozenset([y]), x)
    q = ConjunctiveQuery({
        r: (frozenset([fd0, fd1]), [True, True, False, False], False),
        s: (frozenset([fd2]), [True, False, False], True)
    }, [x, y])
    q_read, values = read_cq_file("../sample_files/CQ/test_read.json", "../sample_files/CQ/json_schema.json")
    assert q_read == q


