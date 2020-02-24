import pytest
from cqapk_to_datalog.file_handle import read_cq_file
from cqapk_to_datalog.data_structures import AtomValue, FunctionalDependency, Atom, ConjunctiveQuery, SequentialProof
from cqapk_to_datalog.algorithms import transitive_closure, atom_plus, gen_attack_graph, all_cycles_weak, \
    atom_attacks_variables, \
    gen_m_graph, sequential_proofs, fd_is_internal, find_bad_internal_fd


@pytest.fixture
def load_sample_1():
    q, values = read_cq_file("testing_files/first_order_rewritable/sample_1.json")
    x = values[0]
    y = values[1]
    z = values[2]
    return q, x, y, z


@pytest.fixture
def load_sample_1_with_atoms(load_sample_1):
    q, x, y, z = load_sample_1
    r = Atom("R", [x, y])
    s = Atom("S", [y, z])
    return q, x, y, z, r, s


def test_transitive_closure(load_sample_1):
    q, x, y, z = load_sample_1
    assert transitive_closure({x}, q.get_all_fd()) == {x, y, z}
    assert transitive_closure({y}, q.get_all_fd()) == {y, z}
    assert transitive_closure({z}, q.get_all_fd()) == {z}


def test_plus(load_sample_1_with_atoms):
    q, x, y, z, r, s = load_sample_1_with_atoms
    assert atom_plus(r, q) == {x}
    assert atom_plus(s, q) == {y}


def test_a_graph(load_sample_1_with_atoms):
    q, x, y, z, r, s = load_sample_1_with_atoms
    a_graph = gen_attack_graph(q)
    assert len(a_graph.edges) == 1 and (r, s) in a_graph.edges


def test_m_graph(load_sample_1_with_atoms):
    q, x, y, z, r, s = load_sample_1_with_atoms
    m_graph = gen_m_graph(q)
    assert len(m_graph.edges) == 1 and (r, s) in m_graph.edges


def test_weak_cycle(load_sample_1):
    q = load_sample_1[0]
    a_graph = gen_attack_graph(q)
    assert all_cycles_weak(a_graph, q) is True



def test_attack_variable(load_sample_1_with_atoms):
    q, x, y, z, r, s = load_sample_1_with_atoms
    assert atom_attacks_variables(r, x, q) is False
    assert atom_attacks_variables(r, y, q) is True
    assert atom_attacks_variables(r, z, q) is True
    assert atom_attacks_variables(s, x, q) is False
    assert atom_attacks_variables(s, y, q) is False
    assert atom_attacks_variables(s, z, q) is True


def test_sequential_proof():
    # TODO
    pass


def test_is_internal():
    # TODO
    pass


def test_is_saturated():
    # TODO
    pass
