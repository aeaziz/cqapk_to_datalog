from pkcqa_to_datalog.data_structures import Atom, ConjunctiveQuery, AtomValue, EqualityAtom, DatalogQuery
from typing import List, Set, Tuple, Dict
from copy import copy

'''
This module is used to rewrite CERTAINITY(q) in Datalog when CERTAINITY(q) is in FO.
generateR0, generateR1 and generateR2 functions generate Datalog rules just as described 
in the section 5.2.2 of the report.
'''


class RewritingData:
    """
    Data structure used to keep information about the atom being treated.
    """

    def __init__(self, q: ConjunctiveQuery, atom: Atom, free_vars: List[AtomValue], index: int):
        self.atom = atom
        self.v = atom.variables()
        self.x = q.get_key(atom)
        self.y = q.get_not_key(atom)
        self.vars_x = q.get_key_vars(atom)
        self.vars_y = q.get_not_key_vars(atom)
        self.vars_z, self.c = generate_z_and_c(self.x, self.y, free_vars, index)


def generate_z_variables(n: int, index: int) -> List[AtomValue]:
    """
    Generates n temporal variables
    :param index:   index used to number rules.
    :param n:   The number of variables to be generated
    :return:    A list containing n variables
    """
    res = []
    for i in range(0, n):
        res.append(AtomValue("Z_" + str(index) + "_" + str(i), True))
    return res


def generate_z_and_c(x: List[AtomValue], y: List[AtomValue], free_vars: List[AtomValue], index: int) -> Tuple[
    List[AtomValue], Dict[AtomValue, AtomValue]]:
    """
    Generates the vector of variables Z and the equality set C. Lets use the notation from the report.
    :param x:           x vector of R(x,y)
    :param y:           y vector of R(x,y)
    :param free_vars:   vars(p)
    :param index:       index used to number rules.
    :return:            Z and C
    """
    z = generate_z_variables(len(y), index)
    c = {}
    seen = set()
    for i in range(len(y)):
        y_i = y[i]
        if not y_i.var or y_i in seen or y_i in x or y_i in free_vars:
            c[z[i]] = y_i
        else:
            z[i] = y_i
            seen.add(y_i)
    return z, c


def rewrite_fo(q: ConjunctiveQuery, top_sort: List[Atom], done: Set[Atom] = None, index: int = 0) -> List[DatalogQuery]:
    """
    Rewrites CERTAINTY(q) when CERTAINTY(q) is in FO.
    :param q:                       A sjfBCQ
    :param top_sort:                A topological sort of the attack graph of q
    :param done:                    A set of the Atom that have already been treated by the rewriting process
    :param index:                   Index used to enumerate the Datalog rules
    :return:                        A list of Datalog rules.
    """
    if done is None:
        done = set()
    free_vars = q.free_vars
    output = []
    atom = top_sort[0]
    vars_without_frozen = []
    for var in atom.variables():
        if var not in vars_without_frozen and var not in free_vars:
            vars_without_frozen.append(var)
    data = RewritingData(q, atom, free_vars, index)
    existential = generateR0(data, done, free_vars, index)
    if len(data.c) == 0 and len(top_sort) == 1:
        return [existential]
    else:
        forall = generateR1(data, done, free_vars, index)
        existential.add_atom(forall.head, True)
        cond = generateR2(data, done, free_vars, index)
        if len(top_sort) == 1:
            forall.add_atom(cond.head, True)
            return [existential, forall, cond]
        else:
            new_q = q.remove_atom(atom)
            for var in data.v:
                new_q = new_q.release_variable(var)
            if len(data.c) == 0:
                next_head = Atom("R_" + str(index + 2), free_vars + vars_without_frozen)
                forall.add_atom(next_head, True)
                return [existential, forall] + rewrite_fo(new_q, top_sort[1:], done.union({atom}), index + 2)
            else:
                next_head = Atom("R_" + str(index + 3), free_vars + vars_without_frozen)
                forall.add_atom(cond.head, True)
                cond.add_atom(next_head, False)
                return [existential, forall, cond] + rewrite_fo(new_q, top_sort[1:], done.union({atom}), index + 3)


def generateR0(data: RewritingData, done: Set[Atom], frozen: List[AtomValue], index: int) -> DatalogQuery:
    if index == 0:
        name = "CERTAINTY"
    else:
        name = "R_" + str(index)
    head = Atom(name, frozen)
    eq = DatalogQuery(head)
    for a_d in done:
        eq.add_atom(a_d)
    eq.add_atom(data.atom)
    return eq


def generateR1(data: RewritingData, done: Set[Atom], frozen: List[AtomValue], index: int) -> DatalogQuery:
    vars_x_not_in_frozen = [var for var in data.vars_x if var not in frozen]
    head = Atom("R_" + str(index + 1), frozen + vars_x_not_in_frozen)
    faq = DatalogQuery(head)
    for a_d in done:
        faq.add_atom(a_d)
    z_atom = Atom(data.atom.name, data.x + data.vars_z)
    faq.add_atom(z_atom)
    return faq


def generateR2(data: RewritingData, done: Set[Atom], frozen: List[AtomValue], index: int) -> DatalogQuery:
    vars_x_not_in_frozen = [var for var in data.vars_x if var not in frozen]
    head = Atom("R_" + str(index + 2), frozen + vars_x_not_in_frozen + data.vars_z)
    cacq = DatalogQuery(head)
    for a_d in done:
        cacq.add_atom(a_d)
    z_atom = Atom(data.atom.name, data.x + data.vars_z)
    cacq.add_atom(z_atom)
    for val in data.c:
        cacq.add_atom(EqualityAtom(val, data.c[val]))
    return cacq
