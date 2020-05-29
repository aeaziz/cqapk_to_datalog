from typing import Set, FrozenSet, List, Dict, Tuple, Union
from copy import copy, deepcopy
from pyDatalog import pyDatalog


class AtomValue:
    """
    Class representing a value belonging to an Atom ie a Variable or a Constant
    """
    def __init__(self, name: str, variable: bool):
        """
        Constructor
        :param name: name of the value
        :param variable: True if the value is a variable, False if it is a constant
        """
        self.name = name
        self.var = variable

    def __str__(self) -> str:
        """
        String representation
        :return: String representation
        """
        return str(self.name)

    def __eq__(self, other: object) -> bool:
        """
        Comparator
        :param other: Another object
        :return: True if the objects are equal, else returns False
        """
        if not isinstance(other, AtomValue):
            return NotImplemented
        return self.name == other.name

    def __repr__(self) -> str:
        """
        String representation
        :return: String representation
        """
        return self.__str__()

    def __hash__(self) -> int:
        """
        Hash method
        :return: Hash value
        """
        return hash(self.name)

class FunctionalDependency:
    """
    Class representing a functional dependency
    """
    def __init__(self, left_vars: List[AtomValue], right_var: AtomValue) -> None:
        """
        Constructor
        :param left_vars: List containing the left-side variables of the FD
        :param right_var: Variable on the right side of the FD
        """
        self.left = frozenset([value for value in left_vars if value.var])
        self.right = right_var

    def __eq__(self, other: object) -> bool:
        """
        Comparator
        :param other: Another object
        :return: True if the objects are equal, else returns False
        """
        if not isinstance(other, FunctionalDependency):
            return NotImplemented
        return self.left == other.left and self.right == other.right

    def __str__(self) -> str:
        """
        String representation
        :return: String representation
        """
        return str(self.left) + " --> " + str(self.right)

    def __repr__(self) -> str:
        """
        String representation
        :return: String representation
        """
        return self.__str__()

    def __hash__(self) -> int:
        """
        Hash method
        :return: Hash value
        """
        return hash((self.left, self.right))

class FunctionalDependencySet:
    def __init__(self, set_def: FrozenSet[FunctionalDependency] = None):
        if set_def is None:
            self.set = frozenset()
        else:
            self.set = set_def

    def add(self, fd: FunctionalDependency) -> None:
        self.set = self.set.union({fd})

    def remove(self, fd: FunctionalDependency) -> None:
        self.set = self.set - {fd}

    def release_variable(self, var: AtomValue) -> 'FunctionalDependencySet':
        new_set = frozenset()
        for fd in self.set:
            left = fd.left - {var}
            if len(left) > 0 and fd.right != var:
                new_set = new_set.union({FunctionalDependency(left, fd.right)})
        return FunctionalDependencySet(new_set)

    def union(self, other: 'FunctionalDependencySet'):
        new = FunctionalDependencySet()
        new.set = self.set.union(other.set)
        return new

    def __eq__(self, other):
        if not isinstance(other, FunctionalDependencySet):
            return NotImplemented
        return self.set == other.set

    def __str__(self):
        return str(self.set)

class Atom:
    """
    Class representing an atom
    """

    def __init__(self, name: str, content: List[AtomValue], released: Set[AtomValue] = None) -> None:
        """
        Constructor
        :param name: Name of the relation
        :param content: List representing the content of the Atom. May contain Variables and Constants
        """
        self.name = name
        self.content = tuple(content)
        if released is None:
            self.released = set()
        else:
            self.released = released

    def variables(self) -> List[AtomValue]:
        """
        Returns the variables in the atom
        :return: A list containing the variables in the atom (In order)
        """
        return [var for var in self.content if var.var and var not in self.released]

    def all_variables(self) -> List[AtomValue]:
        """
        Returns the variables (including released variables) in the atom
        :return: A list containing the variables in the atom (In order)
        """
        return [var for var in self.content if var.var]

    def constants(self) -> List[AtomValue]:
        """
        Returns the constant in the atom
        :return: A list containing the constants in the atom (In order)
        """
        return [con for con in self.content if not con.var or con in self.released]

    def release_variable(self, var: AtomValue) -> 'Atom':
        if var in [v for v in self.content if v.var] and var not in self.released:
            new_var = AtomValue(var.name, False)
            new_content = [v if v != var else new_var for v in self.content]
            return Atom(self.name, new_content, self.released.union({var}))
        else:
            return self

    def __eq__(self, other: object):
        """
        Comparator
        :param other: Another object
        :return: True if the objects are equal, else returns False
        """
        if not isinstance(other, Atom):
            return NotImplemented
        return self.name == other.name and self.content == other.content

    def __str__(self) -> str:
        """
        String representation
        :return: String representation
        """
        if len(self.content) == 0:
            return self.name
        content = ""
        for value in self.content:
            content += str(value) + ","
        return self.name + "(" + content[:-1] + ")"

    def __repr__(self) -> str:
        """
        String representation
        :return: String representation
        """
        return self.__str__()

    def __hash__(self) -> int:
        """
        Hash method
        :return: Hash value
        """
        return hash((self.name, self.content))

class EqualityAtom:
    """
    Datalog representation of an equality (positive or negative) between two Variables/Constants
    """

    def __init__(self, v1: AtomValue, v2: AtomValue, negative=False):
        """
        Constructor
        :param v1: A Variable or Constant
        :param v2: A Variable or Constant
        :param negative: True if the equality is negative
        """
        self.v1 = v1
        self.v2 = v2
        self.negative = negative

    def __str__(self):
        """
        String representation
        :return: String representation
        """
        if self.negative:
            op = "!="
        else:
            op = "="
        return str(self.v1) + op + str(self.v2)

    def __repr__(self):
        """
        String representation
        :return: String representation
        """
        return self.__str__()

    def __hash__(self) -> int:
        """
        Hash method
        :return: Hash value
        """
        return hash((self.negative, (self.v1, self.v2)))

    def __eq__(self, other):
        if not isinstance(other, EqualityAtom):
            return NotImplemented
        return self.v1 == other.v1 and self.v2 == other.v2 and self.negative == other.negative

class CompareAtom:
    """
    Datalog representation of an inequality between two Variables/Constants
    """

    def __init__(self, v1: AtomValue, v2: AtomValue, bigger: bool):
        """
        Constructor
        :param v1: A Variable or Constant
        :param v2: A Variable or Constant
        :param bigger: True if v1 > v2, False if v1 < v2
        """
        self.v1 = v1
        self.v2 = v2
        self.bigger = bigger

    def __str__(self):
        """
        String representation
        :return: String representation
        """
        if self.bigger:
            op = ">"
        else:
            op = "<"
        return str(self.v1) + op + str(self.v2)

    def __repr__(self):
        """
        String representation
        :return: String representation
        """
        return self.__str__()

    def __hash__(self) -> int:
        """
        Hash method
        :return: Hash value
        """
        return hash((self.bigger, (self.v1, self.v2)))

    def __eq__(self, other):
        if not isinstance(other, CompareAtom):
            return NotImplemented
        return self.v1 == other.v1 and self.v2 == other.v2 and self.bigger == other.bigger

class DatalogQuery:
    """
    Class representing a Datalog query
    """

    def __init__(self, head: Atom):
        self.head = head
        self.atoms = set()
        self.neg = {}

    def add_atom(self, atom: Union[Atom, EqualityAtom, CompareAtom], neg: bool = False) -> None:
        """
        Adds an Atom to the query
        :param atom:    Atom object to be added
        :param neg:     True if the instance of Atom in the query should be negative
        """
        self.atoms.add(atom)
        self.neg[atom] = neg

    def remove_atom(self, atom: Atom) -> None:
        """
        Removes an Atom from the query
        :param atom:       Atom object to be removed
        """
        if atom in self.atoms:
            self.atoms.remove(atom)

    def __str__(self):
        body = []
        for atom in self.atoms:
            if self.neg[atom]:
                body.append("not " + str(atom))
            else:
                body.append(str(atom))
        return str(self.head) + " :- " + ', '.join(body) + "."

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if not isinstance(other, DatalogQuery):
            return NotImplemented
        return self.head == other.head and self.atoms == other.atoms and self.neg == other.neg

class ConjunctiveQuery:
    """
    Class representing a Conjunctive Query.
    We consider that a Conjunctive Query is a set of tuples (Atom, Set of FD, Key Positions, Consistent).
    This object also contain a set of free variables (Referred as frozen variables here).
    """

    def __init__(self, content: Dict[Atom, Tuple[FunctionalDependencySet, List[bool], bool]] = None,
                 free_vars: List[AtomValue] = None) -> None:
        if content is None:
            self.content = {}
        else:
            self.content = content
        if free_vars is None:
            self.free_vars = []
        else:
            self.free_vars = free_vars

    def get_atoms(self) -> Set[Atom]:
        """
        Returns all the atoms in the query.
        :return:    A set of Atom objects.
        """
        return set(self.content.keys())

    def get_atom_by_name(self, name: str) -> Atom:
        for atom in self.content:
            if atom.name == name:
                return atom

    def get_all_variables(self) -> Set[AtomValue]:
        """
        Returns all the variables appearing in at least one of the atoms of the query.
        :return:    A Set of variables
        """
        res = set()
        for atom in self.content:
            res = res.union(set(atom.variables()))
        return res

    def get_consistent_atoms(self) -> Set[Atom]:
        """
        Returns only consistent atoms in the query.
        :return:    A set of Atom objects.
        """
        return set([atom for atom in self.content if self.content[atom][2]])

    def get_key(self, atom: Atom) -> List[AtomValue]:
        """
        Returns the values in the key of a given atom
        :param atom:    An Atom object
        :return:        A List of AtomValue objects (Respecting Atom's order).
        """
        if atom in self.content:
            return [atom.content[i] for i in range(len(atom.content)) if self.content[atom][1][i]]

    def get_not_key(self, atom: Atom) -> List[AtomValue]:
        """
        Returns the values that are not in the key of a given atom
        :param atom:    An Atom object
        :return:        A List of AtomValue objects (Respecting Atom's order).
        """
        if atom in self.content:
            return [atom.content[i] for i in range(len(atom.content)) if not self.content[atom][1][i]]

    def get_key_vars(self, atom: Atom, with_free=False) -> List[AtomValue]:
        """
        Returns the variables in the key of a given atom
        :param atom:    An Atom object
        :return:        A List of AtomValue objects containing only variables (Respecting Atom's order).
        """
        if atom in self.content:
            if with_free:
                return [atom.content[i] for i in range(len(atom.content)) if
                        atom.content[i].var and self.content[atom][1][i]]
            else:
                return [atom.content[i] for i in range(len(atom.content)) if
                        atom.content[i] in atom.variables() and self.content[atom][1][i]]

    def get_not_key_vars(self, atom: Atom, with_free=False) -> List[AtomValue]:
        """
        Returns the variables not in the key of a given atom
        :param atom:    An Atom object
        :return:        A List of AtomValue objects containing only variables (Respecting Atom's order).
        """
        if atom in self.content:
            if with_free:
                return [atom.content[i] for i in range(len(atom.content)) if
                        atom.content[i].var and not self.content[atom][1][i]]
            else:
                return [atom.content[i] for i in range(len(atom.content)) if
                        atom.content[i] in atom.variables() and not self.content[atom][1][i]]

    def get_all_fd(self, exclude: Atom = None) -> FunctionalDependencySet:
        """
        Returns all the FunctionalDependencies of this query (Excluding eventually one atom).
        :param exclude:     Atom to be excluded.
        :return:            A FunctionalDependencySet object.
        """
        res = FunctionalDependencySet()
        for atom in self.content:
            if exclude is None or atom != exclude:
                res = res.union(self.content[atom][0])
        return res

    def get_atom_fd(self, atom: Atom) -> FunctionalDependencySet:
        """
        Returns all the FunctionalDependencies of a given Atom.
        :param atom:    An Atom Object.
        :return:        A FunctionalDependencySet object.
        """
        if atom in self.content:
            return self.content[atom][0]

    def is_atom_consistent(self, atom: Atom) -> bool:
        """
        Returns True if the given Atom is consistent.
        :param atom:    An Atom object.
        :return:        True if atom is consistent, False if not.
        """
        if atom in self.content:
            return self.content[atom][2]

    def get_consistent_fd(self) -> FunctionalDependencySet:
        """
        Returns all the FunctionalDependencies of this query that appear in a consistent atom.
        :return:            A FunctionalDependencySet object.
        """
        res = FunctionalDependencySet()
        for atom in self.content:
            if self.content[atom][2]:
                res = res.union(self.content[atom][0])
        return res

    def release_variable(self, var: AtomValue) -> 'ConjunctiveQuery':
        """
        Releases a variable ie. the variable becomes free
        :param var:     A AtomValue object (A variable)
        """
        if var in self.free_vars or not var.var:
            return self
        else:
            new_content = {}
            for atom in self.content:
                new_atom = atom.release_variable(var)
                fd_set = self.content[atom][0].release_variable(var)
                new_content[new_atom] = (fd_set, self.content[atom][1], self.content[atom][2])

        return ConjunctiveQuery(new_content, self.free_vars + [var])

    def remove_atom(self, atom: Atom) -> 'ConjunctiveQuery':
        """
        Given an atom, returns q\{atom}
        :param atom:    Atom to be removed.
        :return         q\{atom}
        """
        if atom not in self.content:
            return self
        new_content = {}
        for key in self.content:
            if key != atom:
                new_content[key] = self.content[key]
        return ConjunctiveQuery(new_content, self.free_vars)

    def add_atom(self, atom: Atom, fd_set: FunctionalDependencySet, is_key: List[bool],
                 is_consistent: True) -> 'ConjunctiveQuery':
        """
        Given an atom, returns q U {atom}.
        :param atom:            Atom to be added.
        :param fd_set:          Set of FunctionalDependency appearing in atom.
        :param is_key:          List of bool such that is_key[i] is True iff the position i of atom belongs to the key.
        :param is_consistent:   True iff atom is consistent.
        :return                 q U {atom}
        """
        if atom in self.content:
            return self
        new_content = copy(self.content)
        new_content[atom] = (fd_set, is_key, is_consistent)
        return ConjunctiveQuery(new_content, self.free_vars)

    def decompose_atom(self, atom: Atom, only_variables : bool = False) -> Tuple[Set[AtomValue],List[AtomValue],List[AtomValue]] :
        v = atom.variables()
        x = self.get_key(atom) if not only_variables else self.get_key_vars(atom)
        y = self.get_not_key(atom) if not only_variables else self.get_not_key_vars(atom)
        return v,x,y
    
    def __copy__(self):
        return ConjunctiveQuery(deepcopy(self.content), deepcopy(self.free_vars))

    def __eq__(self, other):
        if not isinstance(other, ConjunctiveQuery):
            return NotImplemented
        return self.content == other.content and self.free_vars == other.free_vars

    def __str__(self):
        res = ""
        for atom in self.content:
            if self.is_atom_consistent(atom):
                res += "*"
            res += str(atom) + ", "
        return res[:-2]

    def __repr__(self):
        return self.__str__()

class SequentialProof:
    """
    Class representing a Sequential Proof.
    """

    def __init__(self, fd: FunctionalDependency, steps: List[Atom]):
        self.fd = fd
        self.steps = steps

    def is_subset_of(self, other: object) -> bool:
        """
        Returns True iff other is a SequentialProof and is an extension of this SequentialProof
        :param other:   A SequentialProof
        :return:        True iff other is a SequentialProof and is an extension of this SequentialProof, False if not
        """
        if not isinstance(other, SequentialProof):
            return NotImplemented
        return set(self.steps).issubset(other.steps)

    def __eq__(self, other):
        if not isinstance(other, SequentialProof):
            return NotImplemented
        return self.fd == other.fd and set(self.steps) == set(other.steps)

    def __str__(self):
        return str(self.fd) + " : " + str(self.steps)

    def __repr__(self):
        return self.__str__()

class Database:
    def __init__(self):
        self.data = {}

    def get_relations(self) -> List[str]:
        return list(self.data.keys())

    def get_arity(self, relation) -> int:
        if relation in self.data:
            return self.data[relation][0]

    def add_relation(self, relation: str, arity: int):
        if relation not in self.data:
            self.data[relation] = arity, []

    def add_fact(self, relation: str, values: List[Union[str, int]]) -> None:
        if relation not in self.data or self.data[relation][0] == len(values):
            if relation not in self.data:
                self.add_relation(relation, len(values))
            self.data[relation][1].append(values)

    def count_facts(self, relation):
        if relation in self.data:
            return len(self.data[relation][1])     
    
    def __str__(self):
        res = ""
        for relation in self.data:
            for fact in self.data[relation][1]:
                res = res +relation +  "(" + ",".join([str(value) for value in fact]) + ")."
        return(res)

class DatalogProgram:
    def __init__(self, rules: List[DatalogQuery], start_point: int = 0):
        self.rules = rules

    def __str__(self):
        result = ""
        for rule in self.rules:
            result += str(rule) + "\r\n"
        return result

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if not isinstance(other, DatalogProgram):
            return NotImplemented
        if len(self) == len(other):
            for i in range(len(self)):
                if self.rules[i] != other.rules[i]:
                    return False
            return True
        return False

    def __len__(self):
        return len(self.rules)
