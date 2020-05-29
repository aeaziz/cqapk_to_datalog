from cqapk_to_datalog.rewriting import rewrite
from cqapk_to_datalog.parsers.cq_parser import parse_queries_from_file
import sys

def format_output(q):
    free = ""
    if len(q.free_vars) > 0:
        free = "("+",".join(map(lambda x : x.name, q.free_vars))+")"
    output = "\n% Datalog rewriting of CERTAINTY(q"+free+") with q = "+str(q)+"\n"
    output += str(rewrite(q))
    return output


class PrintOutput:
    def save(self, queries):
        for q in queries:
            print(format_output(q))

class FileOutput:
    def __init__(self, file):
        self.file = file
    def save(self, queries):
        file = open(self.file, 'w+')
        for q in queries:
            file.write(format_output(q))

if len(sys.argv) < 2:
    print("Please give a valid file as input")
else:
    file = sys.argv[1]
    output = None
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
        output = FileOutput(output_file)
    else:
        output = PrintOutput()
    queries = parse_queries_from_file(file)
    output.save(queries)


