import sys
import random
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm

sys.path.append('D:\Projects\PYTHON\cqapk_to_datalog')

from cqapk_to_datalog.data_structures import AtomValue, Atom, ConjunctiveQuery, FunctionalDependency, FunctionalDependencySet, DatalogProgram
from cqapk_to_datalog.rewriting import rewrite_fo
from Experiences_Common import TestDatabase
import dlv
import statistics

def generate_rewriting(q, top_sort):	
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

def get_yes_database(q, n_facts):
	relations = [atom.name for atom in q.get_atoms()]
	relations_and_arity = [(atom.name, len(atom.content)) for atom in q.get_atoms()]
	db = TestDatabase(relations_and_arity, n_facts)
	for relation in relations:
		db.add_fact(relation, [0,0])
	for _ in tqdm(range(n_facts), "Building yes database", position = 2, leave= False):
		relation = random.choice(relations)
		value1 = random.choice(range(1,n_facts+1))
		value2 = random.choice(range(1,n_facts+1))
		db.add_fact(relation, [value1, value2])
	return db

def get_no_database(q, n_facts):
	relations = [atom.name for atom in q.get_atoms()]
	relations_and_arity = [(atom.name, len(atom.content)) for atom in q.get_atoms()]
	db = TestDatabase(relations_and_arity, n_facts)
	if len(relations) > 2:
		for i in tqdm(range(n_facts), "Building no database", position = 2, leave= False):
			relation = random.choice(relations)
			db.add_fact(relation, [i, i])
	return db

def build_queries(i, half, q1, q2):
	x = AtomValue("X_"+str(half)+"_"+str(i), True)
	y = AtomValue("X_"+str(half)+"_"+str(i+1), True)
	atom = Atom("R_"+str(half)+"_"+str(i), [x, y])
	fd = FunctionalDependencySet()
	fd.add(FunctionalDependency([x], y))
	q1 = q1.add_atom(atom, fd, [True, False], False)
	q2 = q2.add_atom(atom, fd, [True, False], False)
	return q1, q2


def compare_half(max_n, tries):
	data1 = {
		"n_atoms" : [],
		"sd_plus_yes" : [],
		"sd_minus_yes" : [],
		"mean_yes" : [],
		"sd_plus_no" : [],
		"sd_minus_no" : [],
		"mean_no" : []
	}
	data2 = {
		"n_atoms" : [],
		"sd_plus_yes" : [],
		"sd_minus_yes" : [],
		"mean_yes" : [],
		"sd_plus_no" : [],
		"sd_minus_no" : [],
		"mean_no" : []
	}
	for n in tqdm(range(1, max_n+1), "Queries", position = 1, leave = False):
		data1["n_atoms"].append(n)
		data2["n_atoms"].append(n)
		times_q1_yes = []
		times_q1_no = []
		times_q2_yes = []
		times_q2_no = []
		q1 = ConjunctiveQuery()
		q2_1 = ConjunctiveQuery()
		q2_2 = ConjunctiveQuery()
		for i in tqdm(range(n), "Building q first half", position = 2, leave= False):
			q1, q2_1 = build_queries(i, 1, q1, q2_1)
		for i in tqdm(range(n), "Building q second half", position = 2, leave= False):
			q1, q2_2 = build_queries(i, 2, q1, q2_2)
		top_sort_1 = ["R_1_"+str(i) for i in range(n)]
		top_sort_2 = ["R_2_"+str(i) for i in range(n)]
		program_1 = generate_rewriting(q1, top_sort_1+top_sort_2)
		program_2_1 = generate_rewriting(q2_1, top_sort_1)
		program_2_2 = generate_rewriting(q2_2, top_sort_2)
		db_yes  = get_yes_database(q1, 10)
		db_no = get_no_database(q1, 10)
		for _ in tqdm(range(tries),"Tries", position = 2, leave = False ):
			answer, end_time = dlv.execute_program(program_1, db_yes)
			if len(answer) == 0:
				print("Bad answer : Yes (%s , %s)" % (n, "q1"))
			times_q1_yes.append(end_time)
			answer, end_time1 = dlv.execute_program(program_2_1, db_yes)
			if len(answer) == 0:
				print("Bad answer : Yes (%s , %s)" % (n, "q2_1"))
			answer, end_time2 = dlv.execute_program(program_2_2, db_yes)
			if len(answer) == 0:
				print("Bad answer : Yes (%s , %s)" % (n, "q2_2"))
			times_q2_yes.append(end_time1 + end_time2)

			answer, end_time = dlv.execute_program(program_1, db_no)
			if len(answer) > 0:
				print("Bad answer : No (%s , %s)" % (n, "q1"))
				print(q1)
				print(db_no)
			times_q1_no.append(end_time)
			answer, end_time1 = dlv.execute_program(program_2_1, db_no)
			if len(answer) > 0:
				print("Bad answer : No (%s , %s)" % (n, "q2_1"))
			answer, end_time2 = dlv.execute_program(program_2_2, db_no)
			if len(answer) > 0:
				print("Bad answer : No (%s , %s)" % (n, "q2_2"))
			times_q2_no.append(end_time1 + end_time2)

		data1["sd_plus_yes"].append(statistics.mean(times_q1_yes) + statistics.stdev(times_q1_yes))
		data1["sd_minus_yes"].append(statistics.mean(times_q1_yes) - statistics.stdev(times_q1_yes))
		data1["mean_yes"].append(statistics.mean(times_q1_yes))
		data1["sd_plus_no"].append(statistics.mean(times_q1_no) + statistics.stdev(times_q1_no))
		data1["sd_minus_no"].append(statistics.mean(times_q1_no) - statistics.stdev(times_q1_no))
		data1["mean_no"].append(statistics.mean(times_q1_no))

		data2["sd_plus_yes"].append(statistics.mean(times_q2_yes) + statistics.stdev(times_q2_yes))
		data2["sd_minus_yes"].append(statistics.mean(times_q2_yes) - statistics.stdev(times_q2_yes))
		data2["mean_yes"].append(statistics.mean(times_q2_yes))
		data2["sd_plus_no"].append(statistics.mean(times_q2_no) + statistics.stdev(times_q2_no))
		data2["sd_minus_no"].append(statistics.mean(times_q2_no) - statistics.stdev(times_q2_no))
		data2["mean_no"].append(statistics.mean(times_q2_no))
	
	df1 = pd.DataFrame(data1, columns = ['n_atoms', 'sd_plus_yes', 'sd_minus_yes', 'mean_yes', 'sd_plus_no', 'sd_minus_no', 'mean_no'])
	df2 = pd.DataFrame(data2, columns = ['n_atoms', 'sd_plus_yes', 'sd_minus_yes', 'mean_yes', 'sd_plus_no', 'sd_minus_no', 'mean_no'])
	df1.to_csv("experiences/data_files/exp4/df1.csv")
	df2.to_csv("experiences/data_files/exp4/df2.csv")




def plot(produce = False):
	if produce:
		compare_half(100,10)
	df1 = pd.read_csv("experiences/data_files/exp4/df1.csv")
	df2 = pd.read_csv("experiences/data_files/exp4/df2.csv")
	plt.subplot(1, 2, 1)
	ax = plt.gca()
	df1.plot(x='n_atoms', y='mean_yes', c='blue', ax=ax, label="Execution time for q")
	plt.fill_between(x='n_atoms',y1='sd_minus_yes',y2='sd_plus_yes', data=df1, alpha=0.3)
	df2.plot(x='n_atoms', y='mean_yes', c='red', ax=ax, label="Execution time for q1 + q2")
	plt.fill_between(x='n_atoms',y1='sd_minus_yes',y2='sd_plus_yes', data=df2, alpha=0.3)
	plt.xlabel("# of atoms")
	plt.ylabel("Execution time (s)")
	plt.title("Comparing execution time between q  and q1+q2 (True database)")


	plt.subplot(1, 2, 2)
	ax = plt.gca()
	df1.plot(x='n_atoms', y='mean_no', c='blue', ax=ax, label="Execution time for q")
	plt.fill_between(x='n_atoms',y1='sd_minus_no',y2='sd_plus_no', data=df1, alpha=0.3)
	df2.plot(x='n_atoms', y='mean_no', c='red', ax=ax, label="Execution time for q1 + q2")
	plt.fill_between(x='n_atoms',y1='sd_minus_no',y2='sd_plus_no', data=df2, alpha=0.3)
	plt.xlabel("# of atoms")
	plt.ylabel("Execution time (s)")
	plt.title("Comparing execution time between q  and q1+q2 (False database)")

	plt.show()

plot(True)