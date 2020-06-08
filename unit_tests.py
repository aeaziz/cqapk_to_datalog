import unittest
from cqapk_to_datalog.parsers.cq_parser import parse_queries_from_file
from cqapk_to_datalog.parsers.datalog_parser import read_datalog_file
from cqapk_to_datalog.rewriting import rewrite, saturate
import cqapk_to_datalog.data_structures as structures
import cqapk_to_datalog.algorithms as algorithms


class ReadCQFileTests(unittest.TestCase):
    def setUp(self):
        self.queries = parse_queries_from_file("unit_tests_files/queries.txt")
 
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
        self.program = read_datalog_file("unit_tests_files/query_1.dlog")

    def test_read_is_ok(self):
        x = structures.AtomValue("X", True)
        y = structures.AtomValue("Y", True)
        z = structures.AtomValue("Z", True)
        r = structures.Atom("R", [x,y])
        s = structures.Atom("S", [y,z])
        r_1 = structures.Atom("BadBlock_0", [x])
        r_2 = structures.Atom("RewriteAtom_1", [x,y])
        rule1 = structures.DatalogQuery(structures.Atom("CERTAINTY", []))
        rule1.add_atom(r)
        rule1.add_atom(r_1, True)
        rule2 = structures.DatalogQuery(r_1)
        rule2.add_atom(r)
        rule2.add_atom(r_2, True)
        rule3 = structures.DatalogQuery(r_2)
        rule3.add_atom(r)
        rule3.add_atom(s)
        true_program = structures.DatalogProgram([rule1, rule2, rule3])
        self.assertTrue(self.program == true_program)



class TestAlgosSimpleQuery(unittest.TestCase):
    def setUp(self):
        self.q = parse_queries_from_file("unit_tests_files/queries.txt")[0]
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


class TestAlgosReducibleQuery(unittest.TestCase):
    def setUp(self):
        self.q = parse_queries_from_file("unit_tests_files/queries.txt")[5]
        self.x = structures.AtomValue("X", True)
        self.y = structures.AtomValue("Y", True)
        self.r = structures.Atom("R",[self.x, self.y])
        self.s = structures.Atom("S", [self.y, self.x])

    def test_gen_attack_graph(self):
        a_graph = algorithms.gen_attack_graph(self.q)
        self.assertTrue(len(a_graph.edges) == 2 and (self.r, self.s) in a_graph.edges and (self.s, self.r) in a_graph.edges)

    def test_all_cycles_weak(self):
        a_graph = algorithms.gen_attack_graph(self.q)
        self.assertTrue(algorithms.all_cycles_weak(a_graph, self.q))

    def test_get_reductibel_sets(self):
        a_graph = algorithms.gen_attack_graph(self.q)
        red = algorithms.get_reductible_sets(self.q, a_graph)
        self.assertTrue(red == [[self.r, self.s]] or red == [[self.s, self.r]])

class TestAlgosSaturatedQuery(unittest.TestCase):
    def setUp(self):
        self.q = parse_queries_from_file("unit_tests_files/queries.txt")[7]
        self.other = parse_queries_from_file("unit_tests_files/queries.txt")[1]
        self.z = structures.AtomValue("Z", True)
        self.w = structures.AtomValue("W", True)
        self.fd = structures.FunctionalDependency([self.z],self.w)
        self.t1 = structures.Atom("T_1",[self.z,self.w])
        self.t2 = structures.Atom("T_2",[self.z,self.w])

    def test_sequential_proof(self):
        sp1 = structures.SequentialProof(self.fd, [self.t1])
        sp2 = structures.SequentialProof(self.fd, [self.t2])
        sps = algorithms.sequential_proofs(self.fd, self.q)
        self.assertTrue(sps == [sp1, sp2] or sps == [sp2, sp1])

    def test_is_internal(self):
        self.assertTrue(algorithms.fd_is_internal(self.fd, self.q))

    def test_is_saturated(self):
        self.assertTrue(len(algorithms.find_bad_internal_fd(self.q)) > 0)
        self.assertTrue(len(algorithms.find_bad_internal_fd(self.other)) == 0)

class SaturationTests(unittest.TestCase):
    def setUp(self):
        self.q = parse_queries_from_file("unit_tests_files/queries.txt")[7]
        self.datalog = read_datalog_file("unit_tests_files/query_8.dlog")
 
    def test_is_well_saturated(self):
        bad_fd_set = algorithms.find_bad_internal_fd(self.q)
        self.q, new_rules = saturate(self.q, bad_fd_set)
        new_atom = structures.Atom("N_0",[structures.AtomValue("Z", True), structures.AtomValue("W", True)])
        self.assertTrue(new_atom in self.q.get_consistent_atoms())
        self.assertTrue(structures.DatalogProgram(new_rules) == structures.DatalogProgram(self.datalog.rules[:2]))

class FOTests(unittest.TestCase):
    def setUp(self):
        self.queries = parse_queries_from_file("unit_tests_files/queries.txt")[:5]

    def query_compare(self, i):
        q = self.queries[i]
        program = rewrite(q)
        true_program = read_datalog_file("unit_tests_files/query_"+str(i+1)+".dlog")
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

class CycleReduceTests(unittest.TestCase):
    def setUp(self):
        self.q = parse_queries_from_file("unit_tests_files/queries.txt")[5]

    def test_simple_rewrite(self):
        p = rewrite(self.q)
        p1 = read_datalog_file("unit_tests_files/query_6_1.dlog")
        p2 = read_datalog_file("unit_tests_files/query_6_2.dlog")
        p3 = read_datalog_file("unit_tests_files/query_6_3.dlog")
        p4 = read_datalog_file("unit_tests_files/query_6_4.dlog")
        self.assertTrue(p==p1 or p==p2 or p==p3 or p==p4)

 
if __name__ == '__main__':
    unittest.main()
