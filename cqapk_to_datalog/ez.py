from cqapk_to_datalog.file_handle import read_cq_file
from cqapk_to_datalog.algorithms import find_bad_internal_fd, gen_attack_graph
from cqapk_to_datalog.rewriting_algorithms.saturation import saturate
from cqapk_to_datalog.rewrite import rewrite
import matplotlib.pyplot as plt
import networkx as nx

q = read_cq_file("unit_tests/testing_files/first_order_rewritable/sample_6.json")[0]
print(q)
program = rewrite(q)
print(program)


