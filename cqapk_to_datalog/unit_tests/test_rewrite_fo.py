import unittest
from cqapk_to_datalog.rewriting import rewrite
from cqapk_to_datalog.parsers.cq_parser import parse_queries_from_file
from cqapk_to_datalog.parsers.datalog_parser import read_datalog_file
 
class FOTests(unittest.TestCase):
    def setUp(self):
        self.queries = parse_queries_from_file("cqapk_to_datalog/unit_tests/testing_files/FO.txt")[:5]

    def query_compare(self, i):
        q = self.queries[i]
        program = rewrite(q)
        true_program = read_datalog_file("cqapk_to_datalog/unit_tests/testing_files/query_"+str(i+1)+".dlog")
        self.assertTrue(program == true_program)

    def test_simple_rewrite(self):
        self.query_compare(0)
 
    def test_constant_rewrite(self):
        self.query_compare(1)

    def test_repeated_rewrite(self):
        self.query_compare(2)
 
    def test_free_rewrite(self):
        self.query_compare(3)

    def test_consistent_rewrite(self):
        self.query_compare(4)
 
if __name__ == '__main__':
    unittest.main()
