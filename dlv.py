from subprocess import PIPE, Popen
from cqapk_to_datalog.data_structures import DatalogProgram, Database, DatalogQuery, Atom
import time
import os

def execute_program(dlv_executable: str, program: DatalogProgram, database: Database):
    with open('code.txt', 'w') as the_file:
        the_file.write(str(database)+"\n")
        for rule in program.rules:
            the_file.write(str(rule)+"\n")
    
    start = time.time()
    p = Popen(dlv_executable+' code.txt', shell=True, stdout=PIPE, stderr=PIPE)    
    stdout, stderr = p.communicate()
    end = time.time() - start
    os.remove("code.txt")
    if len(stderr) > 0:
        print(stderr)
    else:
        answers = str(stdout).split("{")[1].split("}")[0].split(', ')
        return [answer for answer in answers if "CERTAINTY" in answer], end

def execute_query(dlv_executable: str,q, db):    
    query = DatalogQuery(Atom("CERTAINTY", []))
    for atom in q.get_atoms():
        query.add_atom(atom)
    program = DatalogProgram([query])
    return execute_program(dlv_executable, program, db)

#execute_program()