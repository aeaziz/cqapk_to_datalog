import unittest
from cqapk_to_datalog.rewriting import rewrite
from cqapk_to_datalog.parsers.cq_parser import parse_queries_from_file
from cqapk_to_datalog.parsers.datalog_parser import read_datalog_file
 
class FOTests(unittest.TestCase):
    def setUp(self):
        self.queries = parse_queries_from_file("cqapk_to_datalog/unit_tests/testing_files/FO.txt")
 
    def test_1(self):
        self.assertTrue(True)
 
    def test_2(self):
        self.assertTrue(True)
 

 
if __name__ == '__main__':
    unittest.main()
