import regex
from cqapk_to_datalog.data_structures import DatalogQuery, Atom, AtomValue, EqualityAtom, CompareAtom, DatalogProgram
from cqapk_to_datalog.exceptions import MalformedQuery


def read_datalog_file(file: str) -> DatalogProgram:
    f = open(file, "r")
    names_regex = "[A-Za-z][A-Za-z0-9_]*"
    atom_regex = names_regex + "(\(" + "(" + names_regex + ",)*" + names_regex + "\))?"
    other_regex = names_regex + "(=|!=|>|<)" + names_regex
    query_element_regex = "(" + other_regex + "|" + "(not )?" + atom_regex + ")"
    query_regex = "^" + atom_regex + " :- " + "(" + query_element_regex + ", )*" + query_element_regex + "\.$"
    queries = []
    line_index = 0
    try:
        for line in f:
            if regex.match(query_regex, line):
                elements = regex.findall(query_element_regex, line)
                head = parse_datalog_atom(elements[0][0])
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
                f.close()
                raise MalformedQuery(line, "DatalogQuery")
    except MalformedQuery:
        f.close()
        raise
    f.close()
    return DatalogProgram(queries)


def parse_atom_value(atom_value_str: str) -> AtomValue:
    """
    Creates an AtomValue object from a string.
    If the value is uppercase, it will be considered as a variable. Otherwise, it will be considered a constant.
    :param atom_value_str:  String representation of the value
    :return:    AtomValue object which string representation is atom_value_str
    """
    return AtomValue(atom_value_str, atom_value_str.isupper())


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
