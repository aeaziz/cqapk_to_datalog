import regex
import os
import cqapk_to_datalog
from cqapk_to_datalog.data_structures import ConjunctiveQuery, DatalogQuery, Atom, AtomValue, EqualityAtom, CompareAtom, \
    FunctionalDependency, DatalogProgram
from typing import List, Tuple
import traceback
import json
from jsonschema import validate
import re


def check_type(value, type_to_check):
    if not isinstance(value, type_to_check):
        raise FormatError("File does not respect format specifications (Wrong type).")


def read_rdb_file(file: str) -> str:
    f = open(file, "r")
    res = ""
    for line in f:
        pattern = re.compile("[A-Z][A-za-z0-9]*\([A-Za-z0-9]+(,[A-Za-z0-9]+)*\).\n")
        if not pattern.match(line):
            raise FormatError("File does not respect format")
        else:
            relation_name, rest = line.split("(")
            res += "+" + relation_name + "("
            body, rest = rest.split(")")
            values = body.split(",")
            i = 0
            for value in values:
                if value.isdigit():
                    res += value
                else:
                    res += "'" + value + "'"
                if i < len(values)-1:
                    res += ","
                i += 1
            res += ") \r\n"
    return res


def read_cq_file(file: str) -> Tuple[ConjunctiveQuery, List[AtomValue]]:
    try:
        validation_file = os.path.dirname(cqapk_to_datalog.__file__)+"/json_schema.json"
        with open(validation_file) as validation_file:
            dict_valid = json.load(validation_file)
        with open(file) as json_file:
            data = json.load(json_file)
            validate(data, dict_valid)
            q = ConjunctiveQuery({}, [])
            atom_values = []
            for value in data["values"]:
                atom_values.append(parse_atom_value(value))
            for var_index in data["free_vars"]:
                value = atom_values[var_index]
                if not value.var:
                    raise FormatError("File does not respect format specifications (Constant given as free variable).")
                q = q.release_variable(value)
            atom_set = {}
            for atom in data["atoms"]:
                content = []
                fd_set = []
                for index in atom["content"]:
                    content.append(atom_values[index])
                for fd in atom["fd"]:
                    left = []
                    for index in fd["left"]:
                        left.append(atom_values[index])
                    fd_set.append(FunctionalDependency(frozenset(left), atom_values[fd["right"]]))
                atom_set[Atom(atom["name"], content)] = (frozenset(fd_set), atom["key"], atom["consistent"])
            for atom in atom_set:
                q = q.add_atom(atom, atom_set[atom][0], atom_set[atom][1], atom_set[atom][2])
            return q, atom_values
    except Exception:
        raise FormatError("File does not respect format specifications.")


def read_datalog_file(file: str) -> DatalogProgram:
    f = open(file, "r")
    names_regex = "[A-Za-z][A-Za-z0-9_]*"
    atom_regex = names_regex + "(\(" + "(" + names_regex + ",)*" + names_regex + "\))?"
    other_regex = names_regex + "(=|!=|>|<)" + names_regex
    query_element_regex = "(" + other_regex + "|" + "(not )?" + atom_regex + ")"
    query_regex = "^" + atom_regex + " :- " + "(" + query_element_regex + ", )*" + query_element_regex + "\.$"
    queries = []
    line_index = 0
    start = 0
    try:
        for line in f:
            if regex.match(query_regex, line):
                elements = regex.findall(query_element_regex, line)
                head = parse_datalog_atom(elements[0][0])
                if head.name == "CERTAINTY":
                    start = line_index
                q = DatalogQuery(head)
                for element in elements[1:]:
                    atom_element = element[0]
                    if "not " in atom_element:
                        q.add_atom(parse_datalog_atom(atom_element[4:]), True)
                    elif "=" in atom_element:
                        q.add_atom(parse_datalog_equality_atom(atom_element))
                    elif ">" in atom_element or "<" in atom_element:
                        q.add_atom(parse_datalog_compare_atom(atom_element))
                    else:
                        q.add_atom(parse_datalog_atom(atom_element))
                queries.append(q)
                line_index += 1
            else:
                raise FormatError("File does not respect format specifications.")
    except FormatError:
        traceback.print_exc()
    return DatalogProgram(queries, start)


def pread_cq_file(file: str) -> ConjunctiveQuery:
    atom_name_regex = "[A-Z][A-Za-z0-9]*"
    value_regex = "(?>[A-Z]+|[a-z]+)"
    values_regex = "(?>" + value_regex + ",)*" + value_regex
    fd_regex = values_regex + "->" + values_regex
    fds_regex = "(?>" + fd_regex + ";)*" + fd_regex
    reg_exp = "^" + atom_name_regex + ':(?>0|1):' + values_regex + ':' + values_regex + '(?>:' + fds_regex + ")?$"
    q = None
    try:
        for line in open(file, 'r'):
            if regex.match("^\[(?>[A-Z]+,)*[A-Z]\]$|^\[\]$", line) and q is None:
                free_var = [parse_atom_value(v) for v in regex.findall(value_regex, line)]
                q = ConjunctiveQuery({}, free_var)
            elif regex.match(reg_exp, line) and q is not None:
                fragments = line.replace("\n", "").split(":")
                atom_name = fragments[0]
                is_consistent = bool(int(fragments[1]))
                key_values = [parse_atom_value(value) for value in fragments[2].split(",")]
                other_values = [parse_atom_value(value) for value in fragments[3].split(",")]
                is_key = [True] * len(key_values) + [False] * len(other_values)
                fds = [parse_fd(fd) for fd in fragments[4].split(";")]
                atom = Atom(atom_name, key_values + other_values)
                q = q.add_atom(atom, frozenset(fds), is_key, is_consistent)
            else:
                raise FormatError("File does not respect format specifications.")
        return q
    except FormatError:
        traceback.print_exc()


def parse_atom_value(atom_value_str: str) -> AtomValue:
    """
    Creates an AtomValue object from a string.
    If the value is uppercase, it will be considered as a variable. Otherwise, it will be considered a constant.
    :param atom_value_str:  String representation of the value
    :return:    AtomValue object which string representation is atom_value_str
    """
    return AtomValue(atom_value_str, atom_value_str.isupper())


def parse_fd(fd_str: str) -> FunctionalDependency:
    """
    Creates a FunctionalDependency object from a string.
    :param fd_str: String representation of the FD
    :return: FunctionalDependency object which string representation is fd_str
    """
    left, right = fd_str.split("->")
    left_vars = [parse_atom_value(var) for var in left.split(",")]
    right_var = parse_atom_value(right)
    return FunctionalDependency(frozenset(left_vars), right_var)


def parse_datalog_atom(atom_str: str) -> Atom:
    """
    Creates an Atom object from a string.
    :param atom_str: String representation of an Atom
    :return: Atom object which string representation is atom_str
    """
    if '(' not in atom_str:
        return Atom(atom_str, [])
    name, body = atom_str.split("(")
    body = body[:-1]
    values = [parse_atom_value(atom_value) for atom_value in body.split(",")]
    return Atom(name, values)


def parse_datalog_equality_atom(atom_str: str) -> EqualityAtom:
    """
    Creates an EqualityAtom object from a string.
    :param atom_str: String representation of an EqualityAtom
    :return: EqualityAtom object which string representation is atom_str
    """
    if "!=" in atom_str:
        v1, v2 = atom_str.split("!=")
        return EqualityAtom(parse_atom_value(v1), parse_atom_value(v2), True)
    else:
        v1, v2 = atom_str.split("=")
        return EqualityAtom(parse_atom_value(v1), parse_atom_value(v2))


def parse_datalog_compare_atom(atom_str: str) -> CompareAtom:
    """
    Creates an CompareAtom object from a string.
    :param atom_str: String representation of an CompareAtom
    :return: CompareAtom object which string representation is atom_str
    """
    if ">" in atom_str:
        v1, v2 = atom_str.split(">")
        return CompareAtom(parse_atom_value(v1), parse_atom_value(v2), True)
    else:
        v1, v2 = atom_str.split("<")
        return CompareAtom(parse_atom_value(v1), parse_atom_value(v2), False)


class FormatError(Exception):
    """
    Exception used to handle bad formed files
    """

    def __init__(self, msg):
        self.msg = msg
