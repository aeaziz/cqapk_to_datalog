from pkcqa_to_datalog import rewrite
from pkcqa_to_datalog.data_structures import AtomValue,Atom,ConjunctiveQuery,FunctionalDependency
# Initialize variables
x = AtomValue("X", True)
y = AtomValue("Y", True)
z = AtomValue("Z", True)
# Initialize atoms
atom_r = Atom("R", [x, y])
atom_s = Atom("S", [y, z])
# Initialize functional dependencies
fd1 = FunctionalDependency(frozenset([x]), y)
fd2 = FunctionalDependency(frozenset([y]), z)
# Initialize the conjunctive query
q = ConjunctiveQuery({}, [])
q = q.release_variable(x)
q = q.add_atom(atom_r, frozenset([fd1]), [True, False], False)
q = q.add_atom(atom_s, frozenset([fd2]), [True, False], False)
rules = rewrite.rewrite(q)
print(rules)
