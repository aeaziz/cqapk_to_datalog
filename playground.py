from cqapk_to_datalog.parsers.cq_parser import parse_queries_from_file
from cqapk_to_datalog.rewriting import rewrite
import cqapk_to_datalog.algorithms as algorithms
from cqapk_to_datalog.data_structures import Database,AtomValue
from experiences.dlv import execute_program
import networkx as nx



q = parse_queries_from_file('cqapk_to_datalog/unit_tests/testing_files/FO.txt')[5]
try:
    program = rewrite(q)
    with open('cqapk_to_datalog/unit_tests/testing_files/query_6_4.dlog', 'w') as the_file:    
        for rule in program.rules:
            the_file.write(str(rule)+'\n')
except Exception:
    print("OK")
