import sys
from tqdm import tqdm
import pandas as pd
import matplotlib.pyplot as plt

sys.path.append('D:\Projects\PYTHON\cqapk_to_datalog')
from exp1 import PathQueryTest, YesDatabase, NoDatabase
from cqapk_to_datalog.data_structures import DatalogProgram, Database
from cqapk_to_datalog.rewriting import rewrite_fo
import dlv
import statistics

def generate_rewriting(q):	
	top_sort = q.get_top_sort()
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

def compare_q_cqa(max_n_atoms, n_facts, tries):
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
	for n_atoms in tqdm(range(1, max_n_atoms + 1), "Queries", position = 0):
		data1["n_atoms"].append(n_atoms)
		data2["n_atoms"].append(n_atoms)
		q = PathQueryTest(n_atoms)
		relations = [(atom.name, len(atom.content)) for atom in q.get_atoms()]
		program = generate_rewriting(q)
		db_yes = YesDatabase(relations, n_facts)
		db_no = NoDatabase(relations, n_facts)
		q_yes_times = []
		cqa_yes_times = []
		q_no_times = []
		cqa_no_times = []
		for _ in tqdm(range(tries), "Executions", position = 1, leave = False):
			answer, end_time = dlv.execute_program(program, db_yes)
			if len(answer) == 0:
				print("Bad answer : Yes (%s, %s)" % (n_atoms, "cqa"))
			cqa_yes_times.append(end_time)

			answer, end_time = dlv.execute_query(q, db_yes)
			if len(answer) == 0:
				print("Bad answer : Yes (%s, %s)" % (n_atoms, "q"))
				print(q)
				print(db_yes)
			q_yes_times.append(end_time)
			
			answer, end_time = dlv.execute_program(program, db_no)
			if len(answer) > 0:
				print("Bad answer : No (%s, %s)" % (n_atoms, "cqa"))
			cqa_no_times.append(end_time)

			answer, end_time = dlv.execute_query(q, db_no)
			if len(answer) > 0:
				print("Bad answer : No (%s, %s)" % (n_atoms, "q"))
			q_no_times.append(end_time)

		data1["sd_plus_yes"].append(statistics.mean(cqa_yes_times) + statistics.stdev(cqa_yes_times))
		data1["sd_minus_yes"].append(statistics.mean(cqa_yes_times) - statistics.stdev(cqa_yes_times))
		data1["mean_yes"].append(statistics.mean(cqa_yes_times))
		data1["sd_plus_no"].append(statistics.mean(cqa_no_times) + statistics.stdev(cqa_no_times))
		data1["sd_minus_no"].append(statistics.mean(cqa_no_times) - statistics.stdev(cqa_no_times))
		data1["mean_no"].append(statistics.mean(cqa_no_times))

		data2["sd_plus_yes"].append(statistics.mean(q_yes_times) + statistics.stdev(q_yes_times))
		data2["sd_minus_yes"].append(statistics.mean(q_yes_times) - statistics.stdev(q_yes_times))
		data2["mean_yes"].append(statistics.mean(q_yes_times))
		data2["sd_plus_no"].append(statistics.mean(q_no_times) + statistics.stdev(q_no_times))
		data2["sd_minus_no"].append(statistics.mean(q_no_times) - statistics.stdev(q_no_times))
		data2["mean_no"].append(statistics.mean(q_no_times))

	df1 = pd.DataFrame(data1, columns = ['n_atoms', 'sd_plus_yes', 'sd_minus_yes', 'mean_yes', 'sd_plus_no', 'sd_minus_no', 'mean_no'])
	df1.to_csv("experiences/data_files/exp5/cqa.csv")
	df2 = pd.DataFrame(data2, columns = ['n_atoms', 'sd_plus_yes', 'sd_minus_yes', 'mean_yes', 'sd_plus_no', 'sd_minus_no', 'mean_no'])
	df2.to_csv("experiences/data_files/exp5/q.csv")

def plot(produce):
	if produce:
		compare_q_cqa(100, 1000, 10)
	df1 = pd.read_csv("experiences/data_files/exp5/cqa.csv")
	df2 = pd.read_csv("experiences/data_files/exp5/q.csv")

	plt.subplot(1, 2, 1)
	ax = plt.gca()
	df1.plot(x='n_atoms', y='mean_yes', c='blue', ax=ax, label="Execution time for CERTAINTY(q)")
	plt.fill_between(x='n_atoms',y1='sd_minus_yes',y2='sd_plus_yes', data=df1, alpha=0.3)
	df2.plot(x='n_atoms', y='mean_yes', c='red', ax=ax, label="Execution time for q")
	plt.fill_between(x='n_atoms',y1='sd_minus_yes',y2='sd_plus_yes', data=df2, alpha=0.3)
	plt.xlabel("# of atoms")
	plt.ylabel("Execution time (s)")
	plt.title("Comparing execution time between q  and CERTAINTY(q) (True database)")


	plt.subplot(1, 2, 2)
	ax = plt.gca()
	df1.plot(x='n_atoms', y='mean_no', c='blue', ax=ax, label="Execution time for CERTAINTY(q)")
	plt.fill_between(x='n_atoms',y1='sd_minus_no',y2='sd_plus_no', data=df1, alpha=0.3)
	df2.plot(x='n_atoms', y='mean_no', c='red', ax=ax, label="Execution time for q")
	plt.fill_between(x='n_atoms',y1='sd_minus_no',y2='sd_plus_no', data=df2, alpha=0.3)
	plt.xlabel("# of atoms")
	plt.ylabel("Execution time (s)")
	plt.title("Comparing execution time between q  and CERTAINTY(q) (False database)")

	plt.show()

plot(True)