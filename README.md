# __cqapk_to_datalog__
__cqapk_to_datalog__ (Consistent Query Answering under Primary Key constraints to Datalog) is a Python 3.x library aiming to provide a tool capable of encoding the problem CERTAINTY(q) into a Datalog program.

# Dependencies
- NetworkX 
    - *pip3 install networkx*
- typing
    - *pip3 install typing*
- tqdm
    - *pip3 install tqdm*
- regex
    - *pip3 install regex*

# Usage
## Batch rewriting
The script 'batch_rewriting.py' allows you to generate the rewriting for a series of sjfBCQ. This script takes as input a file containing the queries in the following format:

[free variables]:RelationName([Key], Other values)

A relation name must always start with a capital letter. Values starting with capital letters are interpreted as variables while values starting with a lower case letter are considered constants.

For example:

[X,Y]:R([X,a],Y),S([Y],Z)


The script can be used with the following command

*python3 batch_rewriting.py input_file*

If a second file is given to the script, the rewritings will be written into that file instead of being printed.

*python3 batch_rewriting.py output_file*

The file 'input_example.txt' is an example of an input file for 'batch_rewriting.py'.


## Import library
The library can directly be imported in your code. The file 'coding_example.py' explains how the library can be used.


# Experiments
To launch the experiments, the executable of DLV is needed. Once downloaded, you just have to give it as input to the script 'experiments.py'

*python3 experiments.py dlv_executable* (Experiments have only been tested on a Windows OS)

