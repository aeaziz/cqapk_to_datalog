## Imports
import sys

sys.path.append('D:\Projects\PYTHON\cqapk_to_datalog')
from cqapk_to_datalog.data_structures import AtomValue, Atom, ConjunctiveQuery, FunctionalDependency, Database, FunctionalDependencySet, DatalogProgram
from cqapk_to_datalog.rewriting import rewrite, rewrite_fo
from typing import List
import numpy as np
import random
import time
from tqdm import tqdm
import os
import itertools
from collections import defaultdict
import math
from Experiences_Common import clear, plot_3D, save_obj, load_obj, plot_2D, TestDatabase
import pandas as pd
import matplotlib.pyplot as plt
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

## Classes
class PathQueryTest(ConjunctiveQuery):
	def __init__(self, n):
		content = {}
		self.n = n
		for i in range(1, n+1):
			x = AtomValue("X_" + str(i - 1), True)
			y = AtomValue("X_" + str(i), True)
			fd = FunctionalDependencySet()
			fd.add(FunctionalDependency(frozenset([x]), y))
			atom = Atom("E_" + str(i), [x, y])
			content[atom] = (fd, [True, False], False)
		ConjunctiveQuery.__init__(self, content)
	
	def get_top_sort(self):
		return ["E_" + str(i) for i in range(1, self.n+1)]

	def get_yes_database(self, n_facts):
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

class YesDatabase(TestDatabase):
	def __init__(self, relations, n_facts):
		TestDatabase.__init__(self, relations, n_facts)
		self.add_true_facts()
		self.generate_facts(n_facts)

	def add_true_facts(self):
		relations = self.get_relations()
		for relation in relations:
			self.blocks[relation][0] = [1]
			self.add_fact(relation, [0,0])            

	def generate_facts(self, n_facts):
		relations = self.get_relations()
		for _ in range(n_facts):
			relation = random.choice(relations)
			block = random.choice(range(1,n_facts+1))
			value = random.choice(range(1,n_facts+1))
			self.add_fact(relation, [block, value])
			if block not in self.blocks[relation]:
				self.blocks[relation][block] = []
			self.blocks[relation][block].append(value)

class NoDatabase(TestDatabase):
	def __init__(self, relations, n_facts):
		TestDatabase.__init__(self, relations, n_facts)
		if len(relations) > 1:
			self.generate_facts(n_facts)      

	def generate_facts(self, n_facts):
		relations = self.get_relations()
		for i in range(n_facts):
			relation = random.choice(relations)
			self.add_fact(relation, [i, i])
			if i not in self.blocks[relation]:
				self.blocks[relation][i] = []
			self.blocks[relation][i].append(i)

## Data produce functions
def evolution_fct_query(query_constructor, min_param, max_param, step_param, tries, n_facts, out_file):
	data = {
		"param" : [],
		"max_exec_time_yes" : [],
		"min_exec_time_yes" : [],
		"mean_exec_time_yes" : [],
		"max_exec_time_no" : [],
		"min_exec_time_no" : [],
		"mean_exec_time_no" : []
	}
	param_list  = []
	param = min_param
	while param <= max_param:
		param_list.append(param)
		param = step_param(param)
	for param in tqdm(param_list, "Parameter", position = 0):
		data["param"].append(param)
		q = query_constructor(param)
		relations = [(atom.name, len(atom.content)) for atom in q.get_atoms()]
		program = DatalogProgram(rewrite_fo(q, q.get_top_sort()))
		#db_yes = YesDatabase(relations, n_facts)
		db_yes = q.get_yes_database(n_facts)
		db_no = NoDatabase(relations, n_facts)
		yes_times = []
		no_times = []
		for _ in tqdm(range(tries), "Executions", position = 1, leave = False):
			answer, end_time = dlv.execute_program(program, db_yes)
			if len(answer) == 0:
				print("Bad answer : Yes (%s)" % (param))
			yes_times.append(end_time)
			
			answer, end_time = dlv.execute_program(program, db_no)
			if len(answer) > 0:
				print("Bad answer : No (%s)" % (param))
			no_times.append(end_time)
		data["max_exec_time_yes"].append(max(yes_times))
		data["min_exec_time_yes"].append(min(yes_times))
		data["mean_exec_time_yes"].append(sum(yes_times)/len(yes_times))
		data["max_exec_time_no"].append(max(no_times))
		data["min_exec_time_no"].append(min(no_times))
		data["mean_exec_time_no"].append(sum(no_times)/len(no_times))
	df = pd.DataFrame(data, columns = ['param', 'max_exec_time_yes', 'min_exec_time_yes', 'mean_exec_time_yes', 'max_exec_time_no', 'min_exec_time_no', 'mean_exec_time_no'])
	df.to_csv(out_file)

def evolution_fct_atoms(max_n_atoms, n_facts, tries):
	data = {
		"n_atoms" : [],
		"sd_plus_yes" : [],
		"sd_minus_yes" : [],
		"mean_yes" : [],
		"sd_plus_no" : [],
		"sd_minus_no" : [],
		"mean_no" : []
	}
	for n_atoms in tqdm(range(1, max_n_atoms + 1), "Queries", position = 0):
		data["n_atoms"].append(n_atoms)
		q = PathQueryTest(n_atoms)
		relations = [(atom.name, len(atom.content)) for atom in q.get_atoms()]
		program = generate_rewriting(q)
		db_yes = YesDatabase(relations, n_facts)
		db_no = NoDatabase(relations, n_facts)
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
		data["sd_plus_yes"].append(statistics.mean(yes_times) + statistics.stdev(yes_times))
		data["sd_minus_yes"].append(statistics.mean(yes_times) - statistics.stdev(yes_times))
		data["mean_yes"].append(statistics.mean(yes_times))
		data["sd_plus_no"].append(statistics.mean(no_times) + statistics.stdev(no_times))
		data["sd_minus_no"].append(statistics.mean(no_times) - statistics.stdev(no_times))
		data["mean_no"].append(statistics.mean(no_times))
	df = pd.DataFrame(data, columns = ['n_atoms', 'sd_plus_yes', 'sd_minus_yes', 'mean_yes', 'sd_plus_no', 'sd_minus_no', 'mean_no'])
	df.to_csv("experiences/data_files/exp1/time_fct_atoms.csv")

def evolution_fct_facts(max_exp_facts, n_atoms, tries):
	data = {
		"n_facts" : [], 
		"mean_exec_time_yes" : [],
		"mean_exec_time_no" : []
		}
	q = PathQueryTest(n_atoms)
	relations = [(atom.name, len(atom.content)) for atom in q.get_atoms()]
	program = DatalogProgram(rewrite_fo(q, q.get_top_sort()))
	for exp_facts in tqdm(range(max_exp_facts), "Databases", position = 0):
		n_facts = 10**exp_facts
		data["n_facts"].append(n_facts) 
		db_yes = YesDatabase(relations, n_facts)
		db_no = NoDatabase(relations, n_facts)
		yes_times = []
		no_times = []
		for _ in tqdm(range(tries), "Executions", position = 1, leave = False):
			'''start_time = time.process_time()
			answer = program.run_program(db_yes).answers[0][0]
			end_time = time.process_time() - start_time
			if not answer:'''
			answer, end_time = dlv.execute_program(program, db_yes)
			if len(answer) == 0:
				print("Bad answer : Yes")
			yes_times.append(end_time)
			'''start_time = time.process_time()
			answer = program.run_program(db_no).answers[0][0]
			end_time = time.process_time() - start_time
			if answer:'''
			answer, end_time = dlv.execute_program(program, db_no)
			if len(answer) > 0:
				print(n_atoms)
				print("Bad answer : No")
			no_times.append(end_time)
		data["mean_exec_time_yes"].append(sum(yes_times)/len(yes_times))
		data["mean_exec_time_no"].append(sum(no_times)/len(no_times))
	df = pd.DataFrame(data, columns = ['n_facts', 'mean_exec_time_yes', 'mean_exec_time_no'])
	df.to_csv("experiences/data_files/exp1/time_fct_facts.csv")

## Experiments
def execution_fct_atoms(produce):
	if produce:
		evolution_fct_atoms(100, 1000, 10)
	df = pd.read_csv("experiences/data_files/exp1/time_fct_atoms.csv")
	ax = plt.gca()
	df.plot(kind='line',x='n_atoms',y='mean_yes',ax=ax)
	plt.fill_between(x='n_atoms',y1='sd_minus_yes',y2='sd_plus_yes', data=df, alpha=0.3)
	df.plot(kind='line',x='n_atoms',y='mean_no',ax=ax)
	plt.fill_between(x='n_atoms',y1='sd_minus_no',y2='sd_plus_no', data=df, alpha=0.3)
	plt.xlabel("# of atoms")
	plt.ylabel("Execution time (s)")
	plt.title("Execution time as function of the number of atoms")
	plt.show()

def execution_fct_facts(produce):
	if produce:
		evolution_fct_facts(6, 20, 10)
	df = pd.read_csv("experiences/data_files/exp1/time_fct_facts.csv")
	ax = plt.gca()
	df.plot(kind='line',x='n_facts',y='mean_exec_time_yes',ax=ax)
	df.plot(kind='line',x='n_facts',y='mean_exec_time_no',ax=ax)
	plt.xlabel("# of atoms")
	plt.ylabel("Execution time")
	#plt.yscale("log")
	plt.title("Execution time as function of the size of the database")
	plt.show()





## Main
execution_fct_atoms(False)
#execution_fct_facts(False)



















def generate_yes_instance(n_relations, mu):
	n_blocks_init = 2
	relations = ["E_"+str(n) for n in range(1, n_relations+1)]
	db = Database()
	#print("mu = "+str(mu))
	n_blocks = n_blocks_init
	for relation in relations:
		n_blocks = generate_yes_instance_rec(db, relation, mu, n_blocks)
	return db


def generate_yes_instance_rec(db, relation, mu, n_blocks):
	n_facts_per_block = math.floor(n_blocks/mu)
	for x in range(n_blocks):
		for y in range(n_facts_per_block):
			db.add_fact(relation, [x,y])
	return n_facts_per_block

def generate_no_instance(n_relations, mu):
	n_blocks_init = 2
	relations = ["E_"+str(n) for n in range(1, n_relations+1)]
	db = Database()
	#print("mu = "+str(mu))
	n_blocks = n_blocks_init
	for relation in relations:
		n_blocks = generate_no_instance_rec(db, relation, mu, n_blocks)
	return db


def generate_no_instance_rec(db, relation, mu, n_blocks):
	n_facts_per_block = math.floor(n_blocks/mu)
	for x in range(n_blocks):
		for y in range(n_facts_per_block):
			db.add_fact(relation, [x,y])
	return n_facts_per_block - 1


def desperate_yes(n_relations, mu):
	relations = ["E_"+str(n) for n in range(1, n_relations+1)]
	db = Database()
	for relation in relations:
		desperate_yes_rec(db, relation, mu)
	return db

def desperate_yes_rec(db, relation, mu):
	for x in range(mu):
		for y in range(mu):
			db.add_fact(relation, [x,y])

def desperate_no(n_relations, mu):
	db = desperate_yes(n_relations, mu)
	relation = "E_" + str(n_relations)
	for y in range(mu):
		db.data[relation][1].remove([mu-1,y])
	return db

def new_exp(n_atoms, tries):
	data = {
		"mu" : [],
		"sd_plus_yes" : [],
		"sd_minus_yes" : [],
		"mean_yes" : [],
		"sd_plus_no" : [],
		"sd_minus_no" : [],
		"mean_no" : []
	}
	for i in tqdm(range(1, 100), "mu", position = 0):
		mu = i
		data["mu"].append(mu)
		q = PathQueryTest(n_atoms)
		program = rewrite(q)
		db_yes = desperate_yes(len(q.get_atoms()), mu)
		db_no = desperate_no(len(q.get_atoms()), mu)
		yes_times = []
		no_times = []
		for _ in tqdm(range(tries), "Executions", position = 1, leave = False):
			answer, end_time = dlv.execute_program(program, db_yes)
			if len(answer) == 0:
				print("Bad answer : Yes (%s)" % (mu))
			yes_times.append(end_time)
			
			answer, end_time = dlv.execute_program(program, db_no)
			if len(answer) > 0:
				print("Bad answer : No (%s)" % (mu))
			no_times.append(end_time)
		data["sd_plus_yes"].append(statistics.mean(yes_times) + statistics.stdev(yes_times))
		data["sd_minus_yes"].append(statistics.mean(yes_times) - statistics.stdev(yes_times))
		data["mean_yes"].append(statistics.mean(yes_times))
		data["sd_plus_no"].append(statistics.mean(no_times) + statistics.stdev(no_times))
		data["sd_minus_no"].append(statistics.mean(no_times) - statistics.stdev(no_times))
		data["mean_no"].append(statistics.mean(no_times))
	df = pd.DataFrame(data, columns = ['mu', 'sd_plus_yes', 'sd_minus_yes', 'mean_yes', 'sd_plus_no', 'sd_minus_no', 'mean_no'])
	df.to_csv("experiences/data_files/exp1/mu.csv")


def mu_experiment(produce):
	if produce:
		new_exp(2, 10)
	df = pd.read_csv("experiences/data_files/exp1/mu.csv")
	ax = plt.gca()
	df.plot(kind='line',x='mu',y='mean_yes',ax=ax)
	plt.fill_between(x='mu',y1='sd_minus_yes',y2='sd_plus_yes', data=df, alpha=0.3)
	df.plot(kind='line',x='mu',y='mean_no',ax=ax)
	plt.fill_between(x='mu',y1='sd_minus_no',y2='sd_plus_no', data=df, alpha=0.3)
	plt.xlabel("mu")
	plt.ylabel("Execution time (s)")
	plt.title("Execution time as function of the number of atoms")
	plt.show()

#mu_experiment(True)

