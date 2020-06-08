import unittest
from cqapk_to_datalog.parsers.cq_parser import parse_queries_from_file
import cqapk_to_datalog.data_structures as structures
import cqapk_to_datalog.algorithms as algorithms

class TestSimpleQuery(unittest.TestCase):
    def setUp(self):
        self.q = parse_queries_from_file("cqapk_to_datalog/unit_tests/testing_files/FO.txt")[0]
        self.x = structures.AtomValue("X", True)
        self.y = structures.AtomValue("Y", True)
        self.z = structures.AtomValue("Z", True)
        self.r = structures.Atom("R",[self.x, self.y])
        self.s = structures.Atom("S", [self.y, self.z])

    def test_tansitive_closure(self):
        self.assertTrue(algorithms.transitive_closure({self.x}, self.q.get_all_fd()) == {self.x, self.y, self.z})
        self.assertTrue(algorithms.transitive_closure({self.y}, self.q.get_all_fd()) == {self.y, self.z})
        self.assertTrue(algorithms.transitive_closure({self.z}, self.q.get_all_fd()) == {self.z})

    def test_plus(self):
        self.assertTrue(algorithms.atom_plus(self.r, self.q) == {self.x})
        self.assertTrue(algorithms.atom_plus(self.s, self.q) == {self.y})

    def test_attack_graph(self):
        a_graph = algorithms.gen_attack_graph(self.q)
        self.assertTrue(len(a_graph.edges) == 1 and (self.r, self.s) in a_graph.edges)

    def test_m_graph(self):
        m_graph = algorithms.gen_m_graph(self.q)
        self.assertTrue(len(m_graph.edges) == 1 and (self.r,self.s) in m_graph.edges)

    def test_weak_cycle(self):
        a_graph = algorithms.gen_attack_graph(self.q)
        self.assertTrue(algorithms.all_cycles_weak(a_graph, self.q))

    def test_attack_variable(self):
        self.assertTrue(algorithms.atom_attacks_variables(self.r, self.x, self.q) is False)
        self.assertTrue(algorithms.atom_attacks_variables(self.r, self.y, self.q) is True)
        self.assertTrue(algorithms.atom_attacks_variables(self.r, self.z, self.q) is True)
        self.assertTrue(algorithms.atom_attacks_variables(self.s, self.x, self.q) is False)
        self.assertTrue(algorithms.atom_attacks_variables(self.s, self.y, self.q) is False)
        self.assertTrue(algorithms.atom_attacks_variables(self.s, self.z, self.q) is True)


class TestReducibleQuery(unittest.TestCase):
    def setUp(self):
        pass

    def test_gen_attack_graph(self):
        pass

    def test_all_cycles_weak(self):
        pass

    def test_get_reductibel_sets(self):
        pass

class TestSaturatedQuery(unittest.TestCase):
    def setUp(self):
        pass

    def test_sequential_proof(self):
        pass

    def test_is_internal(self):
        pass

    def test_is_saturated(self):
        pass


 
if __name__ == '__main__':
    unittest.main()
