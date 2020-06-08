## Imports
from cqapk_to_datalog.data_structures import AtomValue, Atom, ConjunctiveQuery, FunctionalDependency, Database, FunctionalDependencySet, DatalogProgram
from cqapk_to_datalog.rewrite import rewrite
from cqapk_to_datalog.rewriting_algorithms.fo_rewriting import rewrite_fo
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
from dlv import execute_program


## Classes
class FreeQueryTest(ConjunctiveQuery):
    def __init__(self, n, m):
        content = {}
        self.n = n
        self.m = m
        free_vars = []
        for i in range(1, n+1):
            x = AtomValue("X_" + str(i - 1), True)
            y = AtomValue("X_" + str(i), True)
            fd = FunctionalDependencySet()
            fd.add(FunctionalDependency(frozenset([x]), y))
            if i <= m :
                c = AtomValue("C_" + str(i), False)
                free_vars.append(c)
            else:
                c = AtomValue("C_"+str(i), True)
                fd.add(FunctionalDependency(frozenset([x]), c))
            atom = Atom("E_" + str(i), [x, c, y])
            if i <= m :
                atom.released.add(c)
            content[atom] = (fd, [True, False, False], False) 
        ConjunctiveQuery.__init__(self, content)
        self.free_vars = free_vars
    
    def get_top_sort(self):
        return ["E_" + str(i) for i in range(1, self.n+1)]
    
    def get_yes_database(self, n_facts):
        relations = [atom.name for atom in self.get_atoms()]
        relations_and_arity = [(atom.name, len(atom.content)) for atom in self.get_atoms()]
        db = TestDatabase(relations_and_arity, n_facts)
        for relation in relations:
            db.add_fact(relation, [0,0,0])
        for _ in range(n_facts):
            relation = random.choice(relations)
            block = random.choice(range(1,n_facts+1))
            value1 = random.choice(range(1,n_facts+1))
            value2 = random.choice(range(1,n_facts+1))
            db.add_fact(relation, [block, value1, value2])
            if block not in db.blocks[relation]:
                db.blocks[relation][block] = []
            db.blocks[relation][block].append((value1, value2))
        return db
    
    def get_no_database(self, n_facts):
        relations = [atom.name for atom in self.get_atoms()]
        relations_and_arity = [(atom.name, len(atom.content)) for atom in self.get_atoms()]
        db = TestDatabase(relations_and_arity, n_facts)
        if len(relations) > 1:
            for i in range(n_facts):
                relation = random.choice(relations)
                db.add_fact(relation, [i, i, i])
                if i not in db.blocks[relation]:
                    db.blocks[relation][i] = []
                db.blocks[relation][i].append((i,i))
        return db

## Data produce functions
def compare_free_effect(max_n_atoms, max_m_atoms, n_facts, tries):
    data = []
    queries = []
    for _ in range(max_m_atoms+1):
        data.append({
            "n_atoms" : [], 
            "mean_exec_time_yes" : [],
            "mean_exec_time_no" : []
        })
    for n_atoms in tqdm(range(1, max_n_atoms + 1), "# of atoms", position = 0):
        queries = []
        m = 0
        while (m <= max_m_atoms and m <= n_atoms):
            q = FreeQueryTest(n_atoms, m)
            data[m]["n_atoms"].append(n_atoms)
            queries.append(q)
            m = m+1
        m = 0
        for q in tqdm(queries, "# of constants", position = 1, leave = False):
            program = DatalogProgram(rewrite_fo(q, q.get_top_sort()))
            yes_times = []
            no_times = []
            for _ in tqdm(range(tries), "Executions", position = 2, leave = False):
                '''start_time = time.process_time()
                answer = program.run_program(q.get_yes_database(n_facts))                
                end_time = time.process_time() - start_time
                if answer is None:'''
                answer, end_time = execute_program(program, q.get_yes_database(n_facts))
                if len(answer) == 0:
                    print("Bad answer : Yes (%s , %s)" % (n_atoms, m))
                yes_times.append(end_time)
                '''start_time = time.process_time()
                answer = program.run_program(q.get_no_database(n_facts))
                end_time = time.process_time() - start_time
                if answer is not None and answer.answers[0][0]:'''
                answer, end_time = execute_program(program, q.get_no_database(n_facts))
                if len(answer) > 0:
                    print("Bad answer : No (%s , %s)" % (n_atoms, m))
                no_times.append(end_time)
            data[m]["mean_exec_time_yes"].append(sum(yes_times)/len(yes_times))
            data[m]["mean_exec_time_no"].append(sum(no_times)/len(no_times))
            m = m + 1
    m = 0
    for d in data:
        df = pd.DataFrame(d, columns = ['n_atoms', 'mean_exec_time_yes', 'mean_exec_time_no'])
        df.to_csv("data_files/exp3/%s_constants.csv" % (m))
        m = m +1
    

## Experiments

def evo_constants(produce):
    if produce:
        compare_free_effect(10, 2, 100, 10)
    dfs = [pd.read_csv("data_files/exp3/%s_constants.csv" % (m)) for m in range(3)]
    plt.subplot(1, 2, 1)
    ax = plt.gca()
    i = 0
    for df in dfs:
        df.plot(kind='line',x='n_atoms',y='mean_exec_time_yes',ax=ax, label="Query with %s free variables"%(i))
        i = i + 5
    plt.xlabel("# of atoms")
    plt.ylabel("Execution time")
    plt.title("Execution time as function of the number of free variables (Yes-Database)")
    plt.subplot(1, 2, 2)
    ax = plt.gca()
    i = 0
    for df in dfs:
        df.plot(kind='line',x='n_atoms',y='mean_exec_time_no',ax=ax, label="Query with %s constants"%(i))
        i = i + 5
    plt.xlabel("# of atoms")
    plt.ylabel("Execution time")
    plt.title("Execution time as function of the number of free variables (No-Database)")
    plt.show()


evo_constants(False)

