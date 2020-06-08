from cqapk_to_datalog.rewriting import rewrite_fo
from cqapk_to_datalog.data_structures import DatalogProgram, ConjunctiveQuery, Atom, AtomValue, FunctionalDependency, FunctionalDependencySet, Database
import statistics
import random
import pandas as pd
import matplotlib.pyplot as plt


class TestDatabase(Database):
	"""
	Abstract Database
	"""
	def __init__(self, relations, n_facts):
		Database.__init__(self)
		self.blocks = {}
		for relation, arity in relations:
			self.add_relation(relation, arity)
			self.blocks[relation] = {}

def generate_fast_rewriting(q):	
	"""
	Generates FO rewriting without generating attack graph
	"""
	top_sort = q.top_sort
	done = set()
	output = []
	current_q = q
	fo_index = 0
	for i in range(len(top_sort)):
		atom = q.get_atom_by_name(top_sort[i])
		current_q, new_rules = rewrite_fo(current_q, atom, len(top_sort)-1 == i, done, fo_index)
		done.add(atom)
		fo_index += 1
		output += new_rules
	return DatalogProgram(output)

class PathQueryTest(ConjunctiveQuery):
	"""
	Query used on experiments
	"""
	def __init__(self, n, rel_base="E_", var_base="X_"):
		content = {}
		self.n = n
		for i in range(1, n+1):
			x = AtomValue(var_base + str(i - 1), True)
			y = AtomValue(var_base + str(i), True)
			fd = FunctionalDependencySet()
			fd.add(FunctionalDependency(frozenset([x]), y))
			atom = Atom(rel_base + str(i), [x, y])
			content[atom] = (fd, [True, False], False)
		self.top_sort = [rel_base + str(i) for i in range(1, self.n+1)]
		ConjunctiveQuery.__init__(self, content)

	def merge(self, other):
		"""
		Merges two PathQueryTest
		"""
		new_q = PathQueryTest(0)		
		new_content = {**self.content, **other.content}
		new_q.top_sort = self.top_sort + other.top_sort
		ConjunctiveQuery.__init__(new_q, new_content)
		return new_q
		

	def get_yes_database(self, n_facts):
		"""
		Generates a yes_database for this query
		"""
		relations = [atom.name for atom in self.get_atoms()]
		relations_and_arity = [(atom.name, len(atom.content)) for atom in self.get_atoms()]
		db = TestDatabase(relations_and_arity, n_facts)
		for relation in relations:
			db.blocks[relation][0] = [1]
			db.add_fact(relation, [0,0])
		for _ in range(n_facts):
			relation = random.choice(relations)
			block = random.choice(range(1,n_facts+1))
			value = random.choice(range(1,n_facts+1))
			db.add_fact(relation, [block, value])
			if block not in db.blocks[relation]:
				db.blocks[relation][block] = []
			db.blocks[relation][block].append(value)
		return db
	
	def get_no_database(self, n_facts):
		"""
		Generates a no_database for this query
		"""
		relations = [atom.name for atom in self.get_atoms()]
		relations_and_arity = [(atom.name, len(atom.content)) for atom in self.get_atoms()]
		db = TestDatabase(relations_and_arity, n_facts)
		if len(relations) > 1:
			for i in range(n_facts):
				relation = random.choice(relations)
				db.add_fact(relation, [i, i])
				if i not in db.blocks[relation]:
					db.blocks[relation][i] = []
				db.blocks[relation][i].append(i)
		return db

def merge_databases(db1, db2):
	"""
	Merges 2 databases
	"""
	db = Database()
	for relation in db1.data:
		arity, data = db1.data[relation]
		for values in data:
			db.add_fact(relation, values)
	for relation in db2.data:
		arity, data = db2.data[relation]
		for values in data:
			db.add_fact(relation, values)
	return db


def get_data_template():
	"""
	Data template
	"""
	return {
		"n_atoms" : [],
		"sd_plus_yes" : [],
		"sd_minus_yes" : [],
		"mean_yes" : [],
		"sd_plus_no" : [],
		"sd_minus_no" : [],
		"mean_no" : []
	}

def udpate_data(data, yes_times, no_times):
	"""
	Updates data with measured times
	"""
	data["sd_plus_yes"].append(statistics.mean(yes_times) + statistics.stdev(yes_times))
	data["sd_minus_yes"].append(statistics.mean(yes_times) - statistics.stdev(yes_times))
	data["mean_yes"].append(statistics.mean(yes_times))
	data["sd_plus_no"].append(statistics.mean(no_times) + statistics.stdev(no_times))
	data["sd_minus_no"].append(statistics.mean(no_times) - statistics.stdev(no_times))
	data["mean_no"].append(statistics.mean(no_times))

def save_data(data, file):
	"""
	Saves data to a csv file
	"""
	df = pd.DataFrame(data, columns = ['n_atoms', 'sd_plus_yes', 'sd_minus_yes', 'mean_yes', 'sd_plus_no', 'sd_minus_no', 'mean_no'])
	df.to_csv(file)

## Experiments
def plot_single_data(file, label1, label2, x, y, title):
	"""
	Plot Function
	"""
	df = pd.read_csv(file)
	ax = plt.gca()
	df.plot(kind='line',x='n_atoms',y='mean_yes',ax=ax, label=label1)
	plt.fill_between(x='n_atoms',y1='sd_minus_yes',y2='sd_plus_yes', data=df, alpha=0.3)
	df.plot(kind='line',x='n_atoms',y='mean_no',ax=ax, label=label2)
	plt.fill_between(x='n_atoms',y1='sd_minus_no',y2='sd_plus_no', data=df, alpha=0.3)
	plt.xlabel(x)
	plt.ylabel(y)
	plt.title(title)
	plt.show()

def plot_double_data(file1, file2, label1, label2, x, y, title1, title2):
	"""
	Plot Function
	"""
	df1 = pd.read_csv(file1)
	df2 = pd.read_csv(file2)
	plt.subplot(1, 2, 1)
	ax = plt.gca()
	df1.plot(x='n_atoms', y='mean_yes', c='blue', ax=ax, label=label1)
	plt.fill_between(x='n_atoms',y1='sd_minus_yes',y2='sd_plus_yes', data=df1, alpha=0.3)
	df2.plot(x='n_atoms', y='mean_yes', c='red', ax=ax, label=label2)
	plt.fill_between(x='n_atoms',y1='sd_minus_yes',y2='sd_plus_yes', data=df2, alpha=0.3)
	plt.xlabel(x)
	plt.ylabel(y)
	plt.title(title1)


	plt.subplot(1, 2, 2)
	ax = plt.gca()
	df1.plot(x='n_atoms', y='mean_no', c='blue', ax=ax, label=label1)
	plt.fill_between(x='n_atoms',y1='sd_minus_no',y2='sd_plus_no', data=df1, alpha=0.3)
	df2.plot(x='n_atoms', y='mean_no', c='red', ax=ax, label=label2)
	plt.fill_between(x='n_atoms',y1='sd_minus_no',y2='sd_plus_no', data=df2, alpha=0.3)
	plt.xlabel(x)
	plt.ylabel(y)
	plt.title(title2)

	plt.show()

