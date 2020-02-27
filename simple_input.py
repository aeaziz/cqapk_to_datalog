import os
import re
from cqapk_to_datalog.data_structures import AtomValue, Atom, ConjunctiveQuery, FunctionalDependency
from cqapk_to_datalog.rewrite import rewrite


# Exception used for malformed files
class NotAQuery(Exception):
    pass


# True if the file respects the specified format
def is_well_formed(input_string):
    atom_pattern = "\*?[A-Z][A-Za-z0-9_]*\(\[[A-Za-z0-9]+(,[A-Za-z0-9_]+)*\](,[A-Za-z0-9_]+)*\)"
    pattern = re.compile("^\[([A-Za-z0-9_]+(,[A-Za-z0-9_]+)*)?\]:(" + atom_pattern + ")+(," + atom_pattern + ")*$")
    return pattern.match(input_string)


def parse_free_vars(free_string):
    work_string = free_string[1:-2]
    result = []
    for var in work_string.split(","):
        result.append(AtomValue(var, True))
    return result


# Parses an atom
def parse_atom(atom_string):
    work_string = atom_string
    consistent = False
    content = []
    fds = []
    key_bool = []
    if work_string[0] == "*":
        consistent = True
        work_string = work_string[1:]

    key_vars_for_fd = []
    other_vars_for_fd = []
    name, body = work_string.split("(")
    key_values, other_values = body[1:-1].split("]")
    key_var = re.findall("[A-Z]+[A-Z_0-9]*", key_values)
    other_var = re.findall("[A-Z]+[A-Z_0-9]*", other_values)
    for value in key_values.split(","):
        atom_value = AtomValue(value, value in key_var)
        content.append(atom_value)
        key_bool.append(value in key_var)
        if value in key_var:
            key_vars_for_fd.append(atom_value)
    for value in other_values[1:].split(","):
        atom_value = AtomValue(value, value in other_var)
        content.append(atom_value)
        key_bool.append(value in key_var)
        if value in other_var:
            other_vars_for_fd.append(atom_value)

    for var in other_vars_for_fd:
        fds.append(FunctionalDependency(frozenset(key_vars_for_fd), var))
    return Atom(name, content), frozenset(fds), key_bool, consistent


input_string = input("Please enter a query : \n")
input_string = input_string.replace(" ", "")

if not is_well_formed(input_string):
    raise NotAQuery
else:
    q = ConjunctiveQuery({}, [])
    atoms = re.findall("\*?[A-Z]+[A-Za-z0-9_]*\(.*?\)", input_string)
    for a in atoms:
        atom, fds, bool_list, consistent = parse_atom(a)
        q = q.add_atom(atom, fds, bool_list, consistent)
    free_vars_string = re.findall("\[.*?\]:", input_string)
    free_vars = parse_free_vars(free_vars_string[0])

    for var in free_vars:
        q = q.release_variable(var)
    print("\nDatalog rewriting of CERTAINTY(q) with q = "+str(q)+"\n")
    print(rewrite(q))
