import cqapk_to_datalog.algorithms as algorithms
import cqapk_to_datalog.data_structures as structures
import cqapk_to_datalog.rules_templates as templates
import networkx as nx
from typing import List, Tuple, FrozenSet, Set
from cqapk_to_datalog.exceptions import NotSelfJoinFreeQuery, CoNPComplete

def rewrite(q: structures.ConjunctiveQuery) -> structures.DatalogProgram:
	"""
	Main rewriting algorithm.
	Described in README File.
	:param q:   A ConjunctiveQuery.
	:return:    A List of DatalogQueries representing a Datalog program which is the rewriting of CERTAINTY(q).
	"""
	if not algorithms.is_self_join_free(q):
		raise NotSelfJoinFreeQuery
	output_rules = []
	done = set()
	fo_index = 0
	reduction_index = 0
	current_q = q
	a_graph = algorithms.gen_attack_graph(current_q)
	if algorithms.all_cycles_weak(a_graph, current_q):
		while len(a_graph.nodes) > 0:
			not_attacked_atoms = [atom for atom in current_q.get_atoms() if a_graph.in_degree(atom) == 0]
			if len(not_attacked_atoms) > 0:
				atom = not_attacked_atoms[0]
				current_q, new_rules = rewrite_fo(current_q, atom, len(a_graph.nodes) == 1 , done, fo_index)
				done.add(atom)
				fo_index += 1
				output_rules += new_rules
			else:
				bad = algorithms.find_bad_internal_fd(current_q)
				if len(bad) != 0:
					current_q, saturation_rules = saturate(current_q, bad)
					output_rules += saturation_rules
				reductible_cycle = algorithms.get_reductible_sets(current_q, a_graph)[0]
				current_q, new_rules = reduce_cycle(reductible_cycle, current_q, reduction_index)
				reduction_index += 1
				output_rules += new_rules
			a_graph = algorithms.gen_attack_graph(current_q)
		return structures.DatalogProgram(output_rules)
	else:
		raise CoNPComplete

def rewrite_fo(q: structures.ConjunctiveQuery, atom: structures.Atom, is_last : bool, done: Set[structures.Atom], index) -> List[structures.DatalogQuery]:
	"""
	Rewrites CERTAINTY(q) when CERTAINTY(q) is in FO.
	:param q:                       A sjfBCQ
	:param top_sort:                A topological sort of the attack graph of q
	:param done:                    A set of the Atom that have already been treated by the rewriting process
	:param index:                   Index used to enumerate the Datalog rules
	:return:                        A list of Datalog rules.
	"""
	rules = []
	data = templates.RewritingData(q, atom, index, is_last, done)
	rules.append(templates.RewriteAtomQuery(data))
	if data.has_c or not data.is_last:
		rules.append(templates.BadBlockQuery(data))
		if data.has_c:
			rules.append(templates.GoodFactQuery(data))
	new_q = q.remove_atom(atom)
	for var in data.v:
		new_q = new_q.release_variable(var)
	return new_q, rules

def reduce_cycle(cycle: List[structures.Atom], q: structures.ConjunctiveQuery,
				 rewriting_index: int) -> Tuple[structures.ConjunctiveQuery, List[structures.DatalogQuery]]:
	rules = []
	k = len(cycle)
	renamings = algorithms.generate_renaming(2*k + 2, q.get_all_variables())
	rules += [templates.EqQuery(atom, q) for atom in cycle]
	rules += [templates.NeqQuery(atom, q, renamings[0]) for atom in cycle ]
	rules += garbage_set_rules(cycle, q, rewriting_index, renamings)
	rules += new_atoms_rules(cycle, q, rewriting_index, renamings)
	t, n_atoms = new_atoms(cycle, q, rewriting_index, renamings[0])
	new_q = q.add_atom(*t)
	for n_atom in n_atoms:
		new_q = new_q.add_atom(*n_atom)
	for atom in cycle:
		new_q = new_q.remove_atom(atom)
	return new_q, rules

def garbage_set_rules(cycle, q, rewriting_index, renamings):
	rules = []
	rules += [templates.RelevantQuery(atom, q) for atom in cycle]
	rules += [templates.GarbageRelevantQuery(atom, q) for atom in cycle]
	rules += [templates.Any1EmbQuery(cycle, q, rewriting_index, renamings)]
	rules += [templates.Rel1EmbQuery(cycle, q, rewriting_index)]
	rules += [templates.Irr1EmbQuery(cycle, q, rewriting_index, renamings)]
	rules += [templates.Garbage1EmbQuery(atom, cycle, q, rewriting_index, renamings) for atom in cycle]
	rules += [templates.PkQuery(cycle, q, rewriting_index, renamings)]
	rules += [templates.DConBaseQuery(cycle, q, rewriting_index, renamings), templates.DConRecQuery(cycle, q, rewriting_index, renamings)]
	rules += [templates.InLongDCycleQuery(cycle, q, rewriting_index, renamings)]
	rules += [templates.GarbageLongCycleQuery(atom, cycle, q, rewriting_index) for atom in cycle]
	rules += [templates.GarbagePropagateQuery(atom1, atom2, q) for atom1 in cycle for atom2 in cycle if atom1 != atom2]
	return rules

def new_atoms(cycle : List[structures.Atom], q : structures.ConjunctiveQuery, rewriting_index : int, renaming):
	_, x_0, _ = q.decompose_atom(cycle[0])
	x_0_ren = algorithms.apply_renaming_to_atom_values(x_0, renaming)
	n_atoms = []
	t_content = []
	t_released = set()
	for atom in cycle:
		_, x, y = q.decompose_atom(atom)
		n = structures.Atom("N_" + atom.name, x + x_0_ren, atom.released)
		t_released = t_released.union(atom.released)
		fd = structures.FunctionalDependencySet()
		for var in x_0_ren:
			fd.add(structures.FunctionalDependency(x, var))
		is_key = [True]*len(x) + [False]*len(x_0_ren)
		n_atoms.append((n, fd, is_key, True))
		t_content += x
		t_content += y
	t = structures.Atom("T_" + str(rewriting_index), x_0_ren + t_content, t_released)
	fd = structures.FunctionalDependencySet()
	for var in t_content:
		fd.add(structures.FunctionalDependency(x_0_ren, var))
	is_key = [True]*len(x_0_ren) + [False]*len(t_content)
	return (t, fd, is_key, False), n_atoms

def new_atoms_rules(cycle, q, rewriting_index, renamings):
	_, x_0, _ = q.decompose_atom(cycle[0])
	rules = []
	rules += [templates.KeepQuery(atom,q) for atom in cycle]
	rules += [templates.LinkQuery(atom, cycle, q, rewriting_index, renamings[0]) for atom in cycle]
	rules += [templates.TransBaseQuery(cycle, q, rewriting_index, renamings[0])]
	rules += [templates.TransRecQuery(cycle, q, rewriting_index, renamings)]
	if len(x_0) > 1:
		rules += [templates.LowerCompositeQuery(cycle, q, i, rewriting_index, renamings) for i in range(len(cycle))]
	else:
		rules += [templates.LowerSingleQuery(cycle, q, rewriting_index, renamings)]
	rules += [templates.IdentifiedByQuery(cycle, q, rewriting_index, renamings[0])]
	rules += [templates.NQuery(atom, cycle ,q , rewriting_index, renamings[0]) for atom in cycle]
	rules += [templates.TQuery(cycle, q, rewriting_index, renamings[0])]
	return rules

def saturate(q: structures.ConjunctiveQuery, bad_fd: FrozenSet[structures.FunctionalDependency]) -> Tuple[structures.ConjunctiveQuery, List[structures.DatalogQuery]]:
	"""
	Saturates a non saturated query.
	:param q:           A non saturated ConjunctiveQuery.
	:param bad_fd:      Set of internal FD that makes q non saturated
	:return:            A set of Datalog rules. q is also modified.
	"""
	n_index = 0
	atoms = q.get_atoms()
	output = []
	new_q = q
	for fd in bad_fd:
		content = list(fd.left) + [fd.right]
		n_atom = structures.Atom("N_" + str(n_index), content)
		fd_set = structures.FunctionalDependencySet()
		fd_set.add(fd)
		new_q = q.add_atom(n_atom, fd_set, [True] * len(fd.left) + [False], True)
		valuation = algorithms.generate_renaming(1, list(new_q.get_all_variables()))[0]
		n_rule = structures.DatalogQuery(n_atom)
		for atom in atoms:
			n_rule.add_atom(atom)
		bad_atom = structures.Atom("BadFact_" + str(n_index), content)
		n_rule.add_atom(bad_atom, True)
		bad_rule = structures.DatalogQuery(bad_atom)
		for atom in atoms:
			bad_rule.add_atom(atom)
			bad_rule.add_atom(algorithms.apply_renaming_to_atom(atom, valuation))
		for var in fd.left:
			bad_rule.add_atom(structures.EqualityAtom(var, valuation[var]))
		bad_rule.add_atom(structures.EqualityAtom(fd.right, valuation[fd.right], True))
		output += [n_rule, bad_rule]
	return new_q, output














'''
def rewrite(q: structures.ConjunctiveQuery) -> structures.DatalogProgram:
	"""
	Main rewriting algorithm.
	Described in README File.
	:param q:   A ConjunctiveQuery.
	:return:    A List of DatalogQueries representing a Datalog program which is the rewriting of CERTAINTY(q).
	"""
	if not algorithms.is_self_join_free(q):
		raise NotSelfJoinFreeQuery
	saturation_rules = []
	reduction_rules = []
	rewriting_rules = []
	a_graph = algorithms.gen_attack_graph(q)
	if algorithms.all_cycles_weak(a_graph, q):
		bad = algorithms.find_bad_internal_fd(q)
		if len(bad) != 0:
			q, saturation_rules = saturate(q, bad)
		a_cycles = list(nx.algorithms.simple_cycles(a_graph))
		reduction_index = 0
		while len(a_cycles) > 0:
			m_graph = algorithms.gen_m_graph(q)
			m_cycles = nx.simple_cycles(m_graph)
			isccs = algorithms.initial_strong_components(a_graph)
			good_cycles = []
			for cycle in m_cycles:
				for iscc in isccs:
					if set(cycle).issubset(iscc):
						good_cycles.append(cycle)
			print(a_cycles)
			print(good_cycles)
			q, rules = reduce_cycle(good_cycles[0], q, reduction_index)
			reduction_rules += rules
			a_graph = algorithms.gen_attack_graph(q)
			a_cycles = list(nx.algorithms.simple_cycles(a_graph))
			reduction_index += 1
		topological_sort = list(nx.topological_sort(a_graph))
		topological_sort = list(map(lambda x:x.name, topological_sort))
		rewriting_rules += rewrite_fo(q, topological_sort)
		return structures.DatalogProgram(saturation_rules + reduction_rules + rewriting_rules)
	else:
		raise CoNPComplete

def rewrite_fo(q: structures.ConjunctiveQuery, top_sort: List[structures.Atom], done: Set[structures.Atom] = None, index: int = 0) -> List[structures.DatalogQuery]:
	"""
	Rewrites CERTAINTY(q) when CERTAINTY(q) is in FO.
	:param q:                       A sjfBCQ
	:param top_sort:                A topological sort of the attack graph of q
	:param done:                    A set of the Atom that have already been treated by the rewriting process
	:param index:                   Index used to enumerate the Datalog rules
	:return:                        A list of Datalog rules.
	"""
	rules = []
	if done is None:
		done = set()
	rules = []
	atom = q.get_atom_by_name(top_sort[0])
	data = templates.RewritingData(q, atom, index, top_sort, done)
	rules.append(templates.RewriteAtomQuery(data))
	if not data.has_c and data.is_last:
		return rules
	else:
		rules.append(templates.BadBlockQuery(data))
		if data.is_last:
			rules.append(templates.GoodFactQuery(data))
			return rules
		else:
			if data.has_c:
				rules.append(templates.GoodFactQuery(data))
			new_q = q.remove_atom(atom)
			for var in data.v:
				new_q = new_q.release_variable(var)
			new_sort = top_sort[1:]
			return rules + rewrite_fo(new_q, new_sort, done.union({atom}), index + 1)
'''