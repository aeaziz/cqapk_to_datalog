from subprocess import PIPE, Popen
from cqapk_to_datalog.data_structures import DatalogProgram, Database, DatalogQuery, Atom
import time

def execute_program(program: DatalogProgram, database: Database):
    with open('dlv_files\code.txt', 'w') as the_file:
        the_file.write(str(database)+"\n")
        for rule in program.rules:
            the_file.write(str(rule)+"\n")
    
    start = time.time()
    p = Popen('dlv_files\dlv.exe dlv_files\code.txt', shell=True, stdout=PIPE, stderr=PIPE)    
    stdout, stderr = p.communicate()
    end = time.time() - start
    if len(stderr) > 0:
        print(stderr)
    else:
        answers = str(stdout).split("{")[1].split("}")[0].split(', ')
        return [answer for answer in answers if "CERTAINTY" in answer], end

def execute_query(q, db):    
    query = DatalogQuery(Atom("CERTAINTY", []))
    for atom in q.get_atoms():
        query.add_atom(atom)
    program = DatalogProgram([query])
    return execute_program(program, db)

#execute_program()