from cqapk_to_datalog.data_structures import AtomValue, Atom, DatalogProgram, CompareAtom, DatalogQuery, ConjunctiveQuery, \
    FunctionalDependency
from cqapk_to_datalog.file_handle import read_datalog_file, read_cq_file


def test_read_datalog():
    x = AtomValue("X", True)
    y = AtomValue("Y", True)
    z = AtomValue("Z", True)
    true = AtomValue("True", False)
    false = AtomValue("False", False)

    r_atom = Atom("R", [x, y])
    s_atom = Atom("S", [y, z])

    q1 = DatalogQuery(Atom("CERTAINTY", [false]))
    q2_head = Atom("CERTAINTY", [true])
    q1.add_atom(q2_head, True)

    q2 = DatalogQuery(q2_head)
    q2.add_atom(r_atom)
    q3_head = Atom("R_1", [x])
    q2.add_atom(q3_head, True)

    q3 = DatalogQuery(q3_head)
    q3.add_atom(r_atom)
    q4_head = Atom("R_2", [x,y])
    q3.add_atom(q4_head, True)

    q4 = DatalogQuery(q4_head)
    q4.add_atom(r_atom)
    q4.add_atom(s_atom)

    program = DatalogProgram([q1, q2, q3, q4])
    read_program = read_datalog_file("testing_files/first_order_rewritable/sample_1.datalog")
    assert program == read_program


def test_read_cq():
    x = AtomValue("X", True)
    y = AtomValue("Y", True)
    z = AtomValue("Z", True)
    a = AtomValue("a", False)
    b = AtomValue("b", False)
    r = Atom("R", [a, x, y])
    s = Atom("S", [y, z, b])
    fd0 = FunctionalDependency(frozenset([x]), y)
    fd1 = FunctionalDependency(frozenset([y]), z)
    q = ConjunctiveQuery({
        r: (frozenset([fd0]), [True, True, False], False),
        s: (frozenset([fd1]), [True, False, False], False)
    }, [])
    q_read, values = read_cq_file("testing_files/first_order_rewritable/sample_2.json")
    assert q_read == q


