import pytest
from pkcqa_to_datalog.file_handle import read_cq_file
from pkcqa_to_datalog.data_structures import AtomValue, FunctionalDependency, Atom, ConjunctiveQuery, SequentialProof
from pkcqa_to_datalog.algorithms import transitive_closure, atom_plus, gen_attack_graph, all_cycles_weak, atom_attacks_variables, \
    gen_m_graph, sequential_proofs, fd_is_internal, find_bad_internal_fd


@pytest.fixture
def json_schema():
    return "../sample_files/CQ/json_schema.json"


@pytest.fixture
def load_sample_1(json_schema):
    q, values = read_cq_file("../sample_files/CQ/sample_1.json", json_schema)
    x = values[0]
    y = values[1]
    z = values[2]
    return q, x, y, z


@pytest.fixture
def load_sample_2(json_schema):
    q, values = read_cq_file("../sample_files/CQ/sample_2.json", json_schema)
    x = values[0]
    y = values[1]
    b = values[2]
    a = values[3]
    z = values[4]
    v = values[5]
    w = values[6]
    return q, x, y, b, a, z, v, w


@pytest.fixture
def load_sample_3(json_schema):
    q, values = read_cq_file("../sample_files/CQ/sample_3.json", json_schema)
    x = values[0]
    y = values[1]
    z = values[2]
    a = values[3]
    b = values[4]
    return q, x, y, z, a, b


@pytest.fixture
def load_sample_4(json_schema):
    q, values = read_cq_file("../sample_files/CQ/sample_4.json", json_schema)
    x = values[0]
    y = values[1]
    z = values[2]
    a = values[3]
    b = values[4]
    return q, x, y, z, a, b


@pytest.fixture
def load_sample_1_with_atoms(load_sample_1):
    q, x, y, z = load_sample_1
    r = Atom("R", [x, y])
    s = Atom("S", [y, z])
    return q, x, y, z, r, s


@pytest.fixture
def load_sample_2_with_atoms(load_sample_2):
    q, x, y, b, a, z, v, w = load_sample_2
    r = Atom("R", [x, y, a])
    s = Atom("S", [y, b])
    t = Atom("T", [z, v, w])
    return q, x, y, b, a, z, v, w, r, s, t


@pytest.fixture
def load_sample_3_with_atoms(load_sample_3):
    q, x, y, z, a, b = load_sample_3
    r = Atom("R", [x, y, z])
    s = Atom("S", [a, x])
    t = Atom("T", [b, y])
    v = Atom("V", [a, b])
    return q, x, y, z, a, b, r, s, t, v


def test_transitive_closure(load_sample_1, load_sample_2):
    q, x, y, z = load_sample_1
    assert transitive_closure({x}, q.get_all_fd()) == {x, y, z}
    assert transitive_closure({y}, q.get_all_fd()) == {y, z}
    assert transitive_closure({z}, q.get_all_fd()) == {z}
    q, x, y, b, a, z, v, w = load_sample_2
    assert transitive_closure({x}, q.get_all_fd()) == {x, y, b}
    assert transitive_closure({z}, q.get_all_fd()) == {z}
    assert transitive_closure({z, v}, q.get_all_fd()) == {z, v, w}
    assert transitive_closure({x, z, v}, q.get_all_fd()) == {x, y, b, z, v, w}


def test_plus(load_sample_1_with_atoms, load_sample_2_with_atoms):
    q, x, y, z, r, s = load_sample_1_with_atoms
    assert atom_plus(r, q) == {x}
    assert atom_plus(s, q) == {y}
    q, x, y, b, a, z, v, w, r, s, t = load_sample_2_with_atoms
    assert atom_plus(r, q) == {x, y, b}
    assert atom_plus(s, q) == {y}
    assert atom_plus(t, q) == {z, v}


def test_a_graph(load_sample_1_with_atoms, load_sample_2_with_atoms, load_sample_3_with_atoms):
    q, x, y, z, r, s = load_sample_1_with_atoms
    a_graph = gen_attack_graph(q)
    assert len(a_graph.edges) == 1 and (r, s) in a_graph.edges
    q, x, y, b, a, z, v, w, r, s, t = load_sample_2_with_atoms
    a_graph = gen_attack_graph(q)
    assert len(a_graph.edges) == 0
    q, x, y, z, a, b, r, s, t, v = load_sample_3_with_atoms
    a_graph = gen_attack_graph(q)
    edges = [(s, r), (t, r), (t, s), (t, v), (v, r), (v, t)]
    for e in a_graph.edges:
        assert e in edges
    for e in edges:
        assert e in a_graph.edges


def test_m_graph(load_sample_1_with_atoms, load_sample_2_with_atoms, load_sample_3_with_atoms):
    q, x, y, z, r, s = load_sample_1_with_atoms
    m_graph = gen_m_graph(q)
    assert len(m_graph.edges) == 1 and (r, s) in m_graph.edges
    q, x, y, b, a, z, v, w, r, s, t = load_sample_2_with_atoms
    m_graph = gen_m_graph(q)
    assert len(m_graph.edges) == 1 and (r, s) in m_graph.edges
    q, x, y, z, a, b, r, s, t, v = load_sample_3_with_atoms
    m_graph = gen_m_graph(q)
    edges = [(v, t), (v, s), (s, v)]
    for e in m_graph.edges:
        assert e in edges
    for e in edges:
        assert e in m_graph.edges


def test_weak_cycle(load_sample_1, load_sample_2, load_sample_3):
    q = load_sample_1[0]
    a_graph = gen_attack_graph(q)
    assert all_cycles_weak(a_graph, q) is True
    q = load_sample_2[0]
    a_graph = gen_attack_graph(q)
    assert all_cycles_weak(a_graph, q) is True
    q = load_sample_3[0]
    a_graph = gen_attack_graph(q)
    assert all_cycles_weak(a_graph, q) is False


def test_attack_variable(load_sample_1_with_atoms):
    q, x, y, z, r, s = load_sample_1_with_atoms
    assert atom_attacks_variables(r, x, q) is False
    assert atom_attacks_variables(r, y, q) is True
    assert atom_attacks_variables(r, z, q) is True
    assert atom_attacks_variables(s, x, q) is False
    assert atom_attacks_variables(s, y, q) is False
    assert atom_attacks_variables(s, z, q) is True


def test_sequential_proof(load_sample_3_with_atoms):
    q, x, y, z, a, b, r, s, t, v = load_sample_3_with_atoms
    fd = FunctionalDependency(frozenset([a]), z)
    sps = sequential_proofs(fd, q)
    expected_sps = [SequentialProof(fd, [s, t, v, r])]
    assert sps == expected_sps


def test_is_internal(load_sample_4):
    q, x, y, z, a, b = load_sample_4
    fd1 = FunctionalDependency(frozenset([x]), y)
    fd2 = FunctionalDependency(frozenset([x]), z)
    assert fd_is_internal(fd1, q) is False
    assert fd_is_internal(fd2, q) is True


def test_is_saturated(load_sample_4):
    q = load_sample_4[0]
    assert len(find_bad_internal_fd(q)) > 0
    to_change = [atom for atom in q.get_atoms() if atom.name == "S1" or atom.name == "S2"]
    for atom in to_change:
        q.content[atom] = (q.content[atom][0], q.content[atom][1], True)
    assert len(find_bad_internal_fd(q)) == 0
