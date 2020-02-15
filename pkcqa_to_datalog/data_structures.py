from typing import Set, FrozenSet, List, Dict, Tuple, Union
from copy import copy, deepcopy


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
        return self.name

    def __eq__(self, other: object) -> bool:
        """
        Comparator
        :param other: Another object
        :return: True if the objects are equal, else returns False
        """
        if not isinstance(other, AtomValue):
            return NotImplemented
        return self.var == other.var and self.name == other.name

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

    def __init__(self, left_set: FrozenSet[AtomValue], right_var: AtomValue) -> None:
        """
        Constructor
        :param left_set: Set containing the left-side variables of the FD
        :param right_var: Variable on the right side of the FD
        """
        self.left = set()
        for value in left_set:
            if value.var:
                self.left.add(value)
        self.left = frozenset(self.left)
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


class Atom:
    """
    Class representing an atom
    """

    def __init__(self, name: str, content: List[AtomValue]) -> None:
        """
        Constructor
        :param name: Name of the relation
        :param content: List representing the content of the Atom. May contain Variables and Constants
        """
        self.name = name
        self.content = tuple(content)

    def variables(self) -> List[AtomValue]:
        """
        Returns the variables in the atom
        :return: A list containing the variables in the atom (In order)
        """
        return [var for var in self.content if var.var]

    def constants(self) -> List[AtomValue]:
        """
        Returns the constant in the atom
        :return: A list containing the constants in the atom (In order)
        """
        return [con for con in self.content if not con.var]

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
        return self.v1.name + op + self.v2.name

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
        Cosntructor
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
        return self.v1.name + op + self.v2.name

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

    def __init__(self, content: Dict[Atom, Tuple[FrozenSet[FunctionalDependency], List[bool], bool]],
                 free_vars: List[AtomValue]) -> None:
        self.content = content
        self.free_vars = free_vars

    def get_atoms(self) -> Set[Atom]:
        """
        Returns all the atoms in the query.
        :return:    A set of Atom objects.
        """
        return set(self.content.keys())

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

    def get_key_vars(self, atom: Atom) -> List[AtomValue]:
        """
        Returns the variables in the key of a given atom
        :param atom:    An Atom object
        :return:        A List of AtomValue objects containing only variables (Respecting Atom's order).
        """
        if atom in self.content:
            return [atom.content[i] for i in range(len(atom.content)) if
                    atom.content[i].var and self.content[atom][1][i]]

    def get_not_key_vars(self, atom: Atom) -> List[AtomValue]:
        """
        Returns the variables not in the key of a given atom
        :param atom:    An Atom object
        :return:        A List of AtomValue objects containing only variables (Respecting Atom's order).
        """
        if atom in self.content:
            return [atom.content[i] for i in range(len(atom.content)) if
                    not atom.content[i].var and self.content[atom][1][i]]

    def get_all_fd(self, exclude: Atom = None) -> FrozenSet[FunctionalDependency]:
        """
        Returns all the FunctionalDependencies of this query (Excluding eventually one atom).
        :param exclude:     Atom to be excluded.
        :return:            A FrozenSet of FunctionalDependency objects.
        """
        res = frozenset()
        for atom in self.content:
            if exclude is None or atom != exclude:
                res = res.union(self.content[atom][0])
        return res

    def get_atom_fd(self, atom: Atom) -> FrozenSet[FunctionalDependency]:
        """
        Returns all the FunctionalDependencies of a given Atom.
        :param atom:    An Atom Object.
        :return:        A FrozenSet of FunctionalDependency objects.
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

    def get_consistent_fd(self) -> FrozenSet[FunctionalDependency]:
        """
        Returns all the FunctionalDependencies of this query that appear in a consistent atom.
        :return:            A FrozenSet of FunctionalDependency objects.
        """
        res = frozenset()
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
        return ConjunctiveQuery(self.content, self.free_vars+[var])

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

    def add_atom(self, atom: Atom, fd_set: FrozenSet[FunctionalDependency], is_key: List[bool],
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
