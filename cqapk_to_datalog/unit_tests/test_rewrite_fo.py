import pytest
from cqapk_to_datalog.rewriting_algorithms.fo_rewriting import rewrite_fo
from cqapk_to_datalog.file_handle import read_cq_file, read_datalog_file
from cqapk_to_datalog.algorithms import gen_attack_graph


@pytest.fixture
def json_schema():
    return "../sample_files/CQ/json_schema.json"


def compare_with_solution(result, solution):
    assert len(solution) == len(result)
    for i in range(len(solution)):
        assert solution[i] == result[i]


def generate_result(q):
    atoms = []
    a_graph = gen_attack_graph(q)
    while len(a_graph.nodes) > 0:
        not_attacked_atoms = [atom for atom in a_graph.nodes if a_graph.in_degree(atom) == 0]
        atoms.append(not_attacked_atoms[0])
        a_graph.remove_node(not_attacked_atoms[0])
    return rewrite_fo(q, atoms)


def test_simple(json_schema):
    q = read_cq_file("../sample_files/CQ/sample_1.json", json_schema)[0]
    solution = read_datalog_file("../sample_files/Datalog/sample_1.txt")
    compare_with_solution(generate_result(q), solution)


def test_constant(json_schema):
    q = read_cq_file("../sample_files/CQ/sample_5.json", json_schema)[0]
    solution = read_datalog_file("../sample_files/Datalog/sample_5.txt")
    compare_with_solution(generate_result(q), solution)


def test_multiple(json_schema):
    q = read_cq_file("../sample_files/CQ/sample_6.json", json_schema)[0]
    solution = read_datalog_file("../sample_files/Datalog/sample_6.txt")
    compare_with_solution(generate_result(q), solution)
