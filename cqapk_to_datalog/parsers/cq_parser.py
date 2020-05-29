import os
import re
from cqapk_to_datalog.data_structures import AtomValue, Atom, ConjunctiveQuery, FunctionalDependency, FunctionalDependencySet
from cqapk_to_datalog.exceptions import MalformedQuery
from typing import List, Tuple


def parse_atoms(string) -> List[Atom]:
    if string == "":
        return []
    pattern = re.compile("[A-Za-z_0-9]+\(.+\)(,[A-Za-z_0-9]+\(.+\))*$")
    if pattern.match(string):
        try:
            atoms_strings = string.split("),")
            for i in range(len(atoms_strings)-1):
                atoms_strings[i] += ")"
            atoms = []
            for atom_string in atoms_strings:
                atoms.append(parse_atom(atom_string))
            return atoms
        except MalformedQuery:
            raise 
    else:
        raise MalformedQuery(string, "list of Atoms")

def parse_atom(string) -> Tuple[Atom, FunctionalDependencySet, List[bool], bool]:
    pattern = re.compile("[A-Z][A-Za-z_0-9]*\*?\(\[[A-Za-z,_0-9]*\][A-Za-z,_0-9]*\)$")
    if pattern.match(string):
        name, body = string.split("(")
        consistent = False
        if "*" in name:
            name = name.replace("*","")
            consistent = True
        key, rest = body[:-1].split(']')
        key = key[1:]
        if len(rest) > 0:
            rest = rest[1:]
        key_values = parse_atoms_values(key)
        rest_values = parse_atoms_values(rest)
        content = key_values + rest_values
        is_key = [True]*len(key_values) + [False]*len(rest_values)
        return Atom(name, content), parse_fd_set(content, is_key), is_key, consistent
    else:
        raise MalformedQuery(string, "Atom")

def parse_fd_set(content, is_key) -> FunctionalDependencySet:
    fd_set = FunctionalDependencySet()
    key_vars = [content[i] for i in range(len(content)) if is_key[i] and content[i].var]
    other_vars = [value for value in content if value not in key_vars]
    for var in other_vars:
        fd_set.add(FunctionalDependency(key_vars, var))
    return fd_set

def parse_atoms_values(string) -> List[AtomValue]:
    if string == "":
        return []
    pattern = re.compile("[A-Za-z_0-9]+(,[A-Za-z_0-9]+)*$")
    values = []
    if pattern.match(string):
        try:
            for value in string.split(","):
                values.append(parse_atom_value(value))
            return values
        except MalformedQuery:
            raise 
    else:
        raise MalformedQuery(string, "list of AtomValues")

def parse_atom_value(string) -> AtomValue:
    pattern_variable = re.compile("[A-Z][A-Za-z_0-9]*$")
    pattern_str_constant = re.compile("[a-z][A-Za-z_0-9]*$")
    pattern_int_constant = re.compile("[0-9]+$")
    if pattern_variable.match(string):
        return AtomValue(string, True)
    if pattern_str_constant.match(string) or pattern_int_constant.match(string):
        return AtomValue(string, False)
    raise MalformedQuery(string, "AtomValue")
    
def parse_query(string):
    pattern = re.compile("\[[A-Za-z_,0-9]*\]:[A-Za-z_,\(\)\[\]0-9]*$")
    if pattern.match(string):
        try:
            free_var_body, query_body = string.split(":") 
            free_var_body = free_var_body[1:-1]
            free_vars = parse_atoms_values(free_var_body)
            q = ConjunctiveQuery()
            for atom, fd_set, is_key, is_consistent in parse_atoms(query_body):
                q = q.add_atom(atom, fd_set, is_key, is_consistent)
            for value in free_vars:
                if value.var:
                    q = q.release_variable(value)
            return q
        except MalformedQuery:
            raise

    else:
        raise MalformedQuery(string, "ConjunctiveQuery")

def clean_line(string) -> str:
    return string.replace(" ", "").replace("\n", "").replace("\t", "")

def parse_queries_from_file(file_name) -> List[ConjunctiveQuery]:
    file = open(file_name, 'r') 
    queries = []
    for query in file.readlines():
        q = parse_query(clean_line(query))
        queries.append(q)
    return queries



