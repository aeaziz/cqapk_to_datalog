from cqapk_to_datalog.rewriting import rewrite
from cqapk_to_datalog.data_structures import AtomValue, Atom, ConjunctiveQuery, FunctionalDependency, FunctionalDependencySet

# Initialize variables and constants
#       First parameter :   Value
#       Second parameter :  True if variable, False if constant
x = AtomValue("X", True)
y = AtomValue("Y", True)
a = AtomValue("a", False)
z = AtomValue("Z", True)


# Initialize atoms
#       First parameter :   Name of the relation
#       Second parameter :  List of AtomValue in the atom
atom_r = Atom("R", [x, a, y])
atom_s = Atom("S", [y,z])

# Initialize functional dependencies
#       First parameter :   Left side of the FD (List of variables)
#       Second parameter :  Right side of the FD (must be a single variable)
fd1 = FunctionalDependencySet()
fd1.add(FunctionalDependency([x], y))
fd2 = FunctionalDependencySet()
fd2.add(FunctionalDependency([y], z))

# Initialize the conjunctive query
q = ConjunctiveQuery()

# Add atoms to q
#       First parameter :   The atom to be added
#       Second parameter :  The set of FD (must be a frozenset as in the example)
#       Third parameter :   A List of booleans describing the "key positions" of the atom
#       Fourth Parameter :  A boolean that must be True if the atom is consistent, False if not
q = q.add_atom(atom_r, fd1, [True,True,False], False)
q = q.add_atom(atom_s, fd2, [True, False], False)

# Choose free variables (creates a new instance)
q = q.release_variable(x)
q = q.release_variable(y)


# Launch rewriting
program = rewrite(q)

# You can print the Datalog program
print(program)

