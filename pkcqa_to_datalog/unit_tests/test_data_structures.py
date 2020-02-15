from pkcqa_to_datalog.data_structures import AtomValue, FunctionalDependency, Atom


def test_fd():
    left = frozenset([AtomValue("X", True), AtomValue("Y", True)])
    right = AtomValue("Z", True)
    fd1 = FunctionalDependency(left, right)
    fd2 = FunctionalDependency(left, right)
    assert fd1.left == left and fd1.right == right
    assert fd1 == fd2


def test_atom():
    x = AtomValue("X", True)
    y = AtomValue("Y", True)
    r = Atom("R", [x, y])
    s = Atom("S", [y, x])

    assert r.content == (x, y)
    assert r.variables() == [x, y]
    assert (r == s) is False
