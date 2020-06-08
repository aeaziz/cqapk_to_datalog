import unittest
from cqapk_to_datalog.rewriting import saturate
import cqapk_to_datalog.algorithms as algorithms
import cqapk_to_datalog.data_structures as structures
from cqapk_to_datalog.parsers.cq_parser import parse_queries_from_file
from cqapk_to_datalog.parsers.datalog_parser import read_datalog_file
 
class SaturationTests(unittest.TestCase):
    def setUp(self):
        self.q = parse_queries_from_file("cqapk_to_datalog/unit_tests/testing_files/FO.txt")[7]
        self.datalog = read_datalog_file("cqapk_to_datalog/unit_tests/testing_files/query_8.dlog")
 
    def test_is_well_saturated(self):
        bad_fd_set = algorithms.find_bad_internal_fd(self.q)
        self.q, new_rules = saturate(self.q, bad_fd_set)
        new_atom = structures.Atom("N_0",[structures.AtomValue("Z", True), structures.AtomValue("W", True)])
        self.assertTrue(new_atom in self.q.get_consistent_atoms())
        self.assertTrue(structures.DatalogProgram(new_rules) == structures.DatalogProgram(self.datalog.rules[:2]))

        
 
if __name__ == '__main__':
    unittest.main()
