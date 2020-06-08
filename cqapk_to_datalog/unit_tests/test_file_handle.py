import unittest
from cqapk_to_datalog.rewriting import rewrite
import cqapk_to_datalog.data_structures as structures
from cqapk_to_datalog.parsers.cq_parser import parse_queries_from_file
from cqapk_to_datalog.parsers.datalog_parser import read_datalog_file
 
class ReadCQFileTests(unittest.TestCase):
    def setUp(self):
        self.queries = parse_queries_from_file("cqapk_to_datalog/unit_tests/testing_files/FO.txt")
 
    def test_simple_case(self):
        x = structures.AtomValue("X", True)
        y = structures.AtomValue("Y", True)
        z = structures.AtomValue("Z", True)
        r = structures.Atom("R", [x, y])
        s = structures.Atom("S", [y, z])
        fd_set_r = structures.FunctionalDependencySet()
        fd_set_s = structures.FunctionalDependencySet()
        fd_set_r.add(structures.FunctionalDependency([x], y))
        fd_set_s.add(structures.FunctionalDependency([y], z))
        q = structures.ConjunctiveQuery()
        q = q.add_atom(r, fd_set_r, [True, False], False)
        q = q.add_atom(s, fd_set_s, [True, False], False)
        self.assertTrue(q == self.queries[0])

    def test_constant(self):
        q = self.queries[1]
        r = q.get_atom_by_name("R")
        a = r.content[0]
        self.assertTrue(not a.var)

    def test_free_vars(self):
        q = self.queries[3]
        x = structures.AtomValue("X", True)
        self.assertTrue(q.free_vars == [x])

class ReadDatalogFileTests(unittest.TestCase):
    def setUp(self):
        pass

 
if __name__ == '__main__':
    unittest.main()
