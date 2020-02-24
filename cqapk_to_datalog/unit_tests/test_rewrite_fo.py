import pytest
from cqapk_to_datalog.rewriting_algorithms.fo_rewriting import rewrite_fo
from cqapk_to_datalog.file_handle import read_cq_file, read_datalog_file
from cqapk_to_datalog.algorithms import gen_attack_graph
from cqapk_to_datalog.rewrite import rewrite


def compare(query_index):
    q = read_cq_file("testing_files/first_order_rewritable/sample_" + str(query_index) + ".json")[0]
    solution = read_datalog_file("testing_files/first_order_rewritable/sample_" + str(query_index) + ".datalog")
    result = rewrite(q)
    assert solution == result


def test_simple():
    compare(1)


def test_constant():
    compare(2)


def test_multiple():
    compare(3)


def test_free_variables():
    compare(5)


def test_consistent():
    compare(6)
