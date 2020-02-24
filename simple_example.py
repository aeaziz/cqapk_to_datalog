from cqapk_to_datalog import rewrite
from cqapk_to_datalog.data_structures import AtomValue, Atom, ConjunctiveQuery, FunctionalDependency
from cqapk_to_datalog.file_handle import read_rdb_file

# Initialize variables
x = AtomValue("X", True)
y = AtomValue("Y", True)
z = AtomValue("Z", True)
a = AtomValue("a", False)
b = AtomValue("b", False)

# Initialize atoms
atom_r = Atom("R", [x, y])
atom_s = Atom("S", [y, z])

# Initialize functional dependencies
fd1 = FunctionalDependency(frozenset([x]), y)
fd2 = FunctionalDependency(frozenset([y]), z)

# Initialize the conjunctive query
q = ConjunctiveQuery({}, [])

# Choose free variables
q = q.release_variable(x)
q = q.release_variable(y)
q = q.release_variable(z)

# Add atoms to q
q = q.add_atom(atom_r, frozenset([fd1]), [True, False], False)
q = q.add_atom(atom_s, frozenset([fd2]), [True, False], False)

# Launch rewriting
program = rewrite.rewrite(q)

# Run program over an existing database
result = program.run_program(read_rdb_file("databases/db1.rdb"))
print(result)
