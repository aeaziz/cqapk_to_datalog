from cqapk_to_datalog import rewrite
from cqapk_to_datalog.data_structures import AtomValue, Atom, ConjunctiveQuery, FunctionalDependency
from cqapk_to_datalog.file_handle import read_rdb_file

# Initialize variables and constants
#       First parameter :   Value
#       Second parameter :  True if variable, False if constant
x = AtomValue("X", True)
y = AtomValue("Y", True)


# Initialize atoms
#       First parameter :   Name of the relation
#       Second parameter :  List of AtomValue in the atom
atom_r = Atom("R", [x, y])
atom_s = Atom("S", [y, x])

# Initialize functional dependencies
#       First parameter :   Left side of the FD (must be a frozenset as in the example)
#       Second parameter :  Right side of the FD (must be a single variable)
fd1 = FunctionalDependency(frozenset([x]), y)
fd2 = FunctionalDependency(frozenset([y]), x)

# Initialize the conjunctive query
q = ConjunctiveQuery({}, [])

# Add atoms to q
#       First parameter :   The atom to be added
#       Second parameter :  The set of FD (must be a frozenset as in the example)
#       Third parameter :   A List of booleans describing the "key positions" of the atom
#       Fourth Parameter :  A boolean that must be True if the atom is consistent, False if not
q = q.add_atom(atom_r, frozenset([fd1]), [True, False], False)
q = q.add_atom(atom_s, frozenset([fd2]), [True, False], False)

# Choose free variables
q = q.release_variable(x)
'''q = q.release_variable(y)
q = q.release_variable(z)
q = q.release_variable(w)'''

# Launch rewriting
program = rewrite.rewrite(q)

# You can print the Datalog program
print(program)

# Or run the program over an existing database
# result = program.run_program(read_rdb_file("databases/db1.rdb"))
# print(result)
