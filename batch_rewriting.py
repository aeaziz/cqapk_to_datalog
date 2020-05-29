from cqapk_to_datalog.rewriting import rewrite
from cqapk_to_datalog.parsers.cq_parser import parse_queries_from_file
import sys

class PrintOutput:
    def save(self, queries):
        for q in queries:
            print("\nDatalog rewriting of CERTAINTY(q) with q = "+str(q)+"\n")
            print(rewrite(q))

class FileOutput:
    def __init__(self, file):
        self.file = file
    def save(self, queries):
        file = open(self.file, 'w+')
        for q in queries:
            file.write("\nDatalog rewriting of CERTAINTY(q) with q = "+str(q)+"\n")
            file.write(str(rewrite(q)))

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


