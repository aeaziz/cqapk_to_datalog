import unittest
from cqapk_to_datalog.rewriting import rewrite
from cqapk_to_datalog.parsers.cq_parser import parse_queries_from_file
from cqapk_to_datalog.parsers.datalog_parser import read_datalog_file
 
class CycleReduceTests(unittest.TestCase):
    def setUp(self):
        self.q = parse_queries_from_file("cqapk_to_datalog/unit_tests/testing_files/FO.txt")[5]

    def test_simple_rewrite(self):
        p = rewrite(self.q)
        p1 = read_datalog_file("cqapk_to_datalog/unit_tests/testing_files/query_6_1.dlog")
        p2 = read_datalog_file("cqapk_to_datalog/unit_tests/testing_files/query_6_2.dlog")
        p3 = read_datalog_file("cqapk_to_datalog/unit_tests/testing_files/query_6_3.dlog")
        p4 = read_datalog_file("cqapk_to_datalog/unit_tests/testing_files/query_6_4.dlog")
        self.assertTrue(p==p1 or p==p2 or p==p3 or p==p4)


 

 
if __name__ == '__main__':
    unittest.main()
