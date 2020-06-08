import experiments_utils
from tqdm import tqdm
import dlv
import statistics


def generate_exp1_data(max_n_atoms, n_facts, tries):
	data = experiments_utils.get_data_template()
	for n_atoms in tqdm(range(1, max_n_atoms + 1), "Queries", position = 0):
		data["n_atoms"].append(n_atoms)
		q = experiments_utils.PathQueryTest(n_atoms)
		relations = [(atom.name, len(atom.content)) for atom in q.get_atoms()]
		program = experiments_utils.generate_fast_rewriting(q)
		db_yes = q.get_yes_database(n_facts)
		db_no = q.get_no_database(n_facts)
		yes_times = []
		no_times = []
		for _ in tqdm(range(tries), "Executions", position = 1, leave = False):
			answer, end_time = dlv.execute_program(program, db_yes)
			if len(answer) == 0:
				print("Bad answer : Yes (%s)" % (n_atoms))
			yes_times.append(end_time)
			
			answer, end_time = dlv.execute_program(program, db_no)
			if len(answer) > 0:
				print("Bad answer : No (%s)" % (n_atoms))
			no_times.append(end_time)
			#input()
		experiments_utils.udpate_data(data, yes_times, no_times)
	experiments_utils.save_data(data, "experiments_files/exp1.csv")

def generate_exp2_data(max_n_atoms, n_facts, tries):
	data1 = experiments_utils.get_data_template()
	data2 = experiments_utils.get_data_template()
	for n_atoms in tqdm(range(1, max_n_atoms + 1), "Queries", position = 0):
		data1["n_atoms"].append(n_atoms)
		data2["n_atoms"].append(n_atoms)
		q = experiments_utils.PathQueryTest(n_atoms)
		relations = [(atom.name, len(atom.content)) for atom in q.get_atoms()]
		program = experiments_utils.generate_fast_rewriting(q)
		db_yes = q.get_yes_database(n_facts)
		db_no = q.get_no_database(n_facts)
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

		experiments_utils.udpate_data(data1, cqa_yes_times, cqa_no_times)
		experiments_utils.udpate_data(data2, q_yes_times, q_no_times)

	experiments_utils.save_data(data1, "experiments_files/exp2_1.csv")
	experiments_utils.save_data(data2, "experiments_files/exp2_2.csv")

def generate_exp3_data(max_n, tries):
	data1 = experiments_utils.get_data_template()
	data2 = experiments_utils.get_data_template()
	for n in tqdm(range(1, max_n+1), "Queries", position = 1, leave = False):
		data1["n_atoms"].append(n)
		data2["n_atoms"].append(n)
		times_q1_yes = []
		times_q1_no = []
		times_q2_yes = []
		times_q2_no = []
		q2_1 = experiments_utils.PathQueryTest(n, "R_", "X_")
		q2_2 = experiments_utils.PathQueryTest(n, "S_", "Y_")
		q1 = q2_1.merge(q2_2)
		top_sort_1 = ["R_1_"+str(i) for i in range(n)]
		top_sort_2 = ["R_2_"+str(i) for i in range(n)]
		program_1 = experiments_utils.generate_fast_rewriting(q1)
		program_2_1 = experiments_utils.generate_fast_rewriting(q2_1)
		program_2_2 = experiments_utils.generate_fast_rewriting(q2_2)
		db_yes  = experiments_utils.merge_databases(q2_1.get_yes_database(5), q2_2.get_yes_database(5))
		db_no = experiments_utils.merge_databases(q2_1.get_no_database(5), q2_2.get_no_database(5))
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

		experiments_utils.udpate_data(data1, times_q1_yes, times_q1_no)
		experiments_utils.udpate_data(data2, times_q2_yes, times_q2_no)
	
	experiments_utils.save_data(data1, "experiments_files/exp3_1.csv")
	experiments_utils.save_data(data2, "experiments_files/exp3_2.csv")



def experiment1(generate_data):
	"""
	Comparing CERTAINTY(q) over yes and no database instances
	"""
	if generate_data:
		generate_exp1_data(100, 1000, 10)
	experiments_utils.plot_single_data(
		"experiments_files/exp1.csv", 
		"Mean execution time over yes instance", 
		"Mean execution time over no instance",
		"# of atoms",
		"Execution time (s)",
		"Execution time as function of the number of atoms"
	)

def experiment2(generate_data):
	"""
	Comparing q and CERTAINTY(q)
	"""
	if generate_data:
		generate_exp2_data(100, 1000, 10)
	experiments_utils.plot_double_data(
		"experiments_files/exp2_1.csv",
		"experiments_files/exp2_2.csv",
		"Execution time for CERTAINTY(q)",
		"Execution time for q",
		"# of atoms",
		"Execution time (s)",
		"Comparing execution time between q  and CERTAINTY(q) (True database)",
		"Comparing execution time between q  and CERTAINTY(q) (False database)"
	)

def experiment3(generate_data):
	"""
	Comparing CERTAINTY(q1+q2) against CERTAINTY(q1)+CERTAINTY(q2)
	"""
	if generate_data:
		generate_exp3_data(100,10)
	experiments_utils.plot_double_data(
		"experiments_files/exp3_1.csv",
		"experiments_files/exp3_2.csv",
		"Execution time for CERTAINTY(q1+q2)",
		"Execution time for CERTAINTY(q1)+CERTAINTY(q2)",
		"# of atoms",
		"Execution time (s)",
		"Comparing CERTAINTY(q1+q2) and CERTAINTY(q1)+CERTAINTY(q2) (True database)",
		"Comparing CERTAINTY(q1+q2) and CERTAINTY(q1)+CERTAINTY(q2) (False database)"
	)

experiment1(False)
experiment2(False)
experiment3(False)
