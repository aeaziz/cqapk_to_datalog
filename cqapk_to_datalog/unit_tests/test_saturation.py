import unittest
from cqapk_to_datalog.rewriting import saturate
import cqapk_to_datalog.algorithms as algorithms
from cqapk_to_datalog.parsers.cq_parser import parse_queries_from_file
from cqapk_to_datalog.parsers.datalog_parser import read_datalog_file
 
class SaturationTests(unittest.TestCase):
    def setUp(self):
        self.q = parse_queries_from_file("cqapk_to_datalog/unit_tests/testing_files/FO.txt")[0]
 
    def test_is_well_saturated(self):
        bad_fd_set = algorithms.find_bad_internal_fd(self.q)
        rules = []
        for bad_fd in bad_fd_set:
            self.q, new_rules = saturate(self.q, bad_fd)
            rules += new_rules
 
if __name__ == '__main__':
    unittest.main()
