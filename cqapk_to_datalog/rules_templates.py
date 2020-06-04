from cqapk_to_datalog.data_structures import DatalogQuery, Atom, EqualityAtom, CompareAtom, ConjunctiveQuery, AtomValue
from cqapk_to_datalog.algorithms import apply_renaming_to_atom, apply_renaming_to_atom_values, generate_new_variables
from typing import List, Set, Tuple, Dict


def generate_z_and_c(x: List[AtomValue], y: List[AtomValue], vars_y: List[AtomValue], index: int) \
        -> Tuple[List[AtomValue], Dict[AtomValue, AtomValue]]:
    """
    Generates the vector of variables Z and the equality set C. 
    :param x:           x vector of R(x,y)
    :param y:           y vector of R(x,y)
    :param vars_y:      vars(y)
    :param index:       index used to number rules.
    :return:            Z and C
    """
    z = generate_new_variables("Z", len(y), index)
    c = {}
    seen = set()
    for i in range(len(y)):
        y_i = y[i]
        if y_i not in vars_y or y_i in seen or y_i in x:
            c[z[i]] = y_i
        else:
            z[i] = y_i
            seen.add(y_i)
    return z, c


class RewritingData:
    """
    Data structure used to keep information about the atom being treated.
    """
    def __init__(self, q: ConjunctiveQuery, atom: Atom, index: int, is_last: bool, done: Set[Atom]):
        self.q = q
        self.atom = atom
        self.index = index
        self.v, self.x, self.y = q.decompose_atom(atom)
        _, self.vars_x, self.vars_y = q.decompose_atom(atom, True)
        self.vars_z, self.c = generate_z_and_c(self.x, self.y, self.vars_y, index)
        self.has_c = len(self.c) > 0
        self.is_last = is_last
        self.frozen = q.free_vars
        self.new_frozen = []
        for var in q.free_vars:
            self.new_frozen.append(var)
        for var in self.v:
            if var not in self.new_frozen:
                self.new_frozen.append(var)
        self.done = done


class FORewritingQuery(DatalogQuery):
    """
    Abstract class for FO Rewriting rules.
    """
    def __init__(self, head : Atom, done: Set[Atom]):
        DatalogQuery.__init__(self, head)
        for a_d in done:
            self.add_atom(a_d)

    def make_safe(self, q: ConjunctiveQuery):
        """
        Adds atoms to make safe the rule
        :param q:       A ConjunctiveQuery
        """
        i = 0
        atoms = list(self.atoms)
        for var in self.head.all_variables():
            k = 0
            while k < len(atoms) and (
                    not isinstance(atoms[k], Atom) or self.neg[atoms[k]] or var not in atoms[k].content):
                k += 1
            if k == len(atoms):
                for atom in q.get_atoms():
                    content = atom.content
                    if var in content:
                        new_vars = generate_new_variables("F", len(content) - 1, i)
                        new_content = []
                        j = 0
                        for value in content:
                            if value != var:
                                new_content.append(new_vars[j])
                                j += 1
                            else:
                                new_content.append(var)
                        new_atom = Atom(atom.name, new_content)
                        new_atom.released = set(new_content).intersection(self.head.content)
                        self.add_atom(new_atom)
                        break
            i += 1


class RewriteAtomQuery(FORewritingQuery):
    def __init__(self, data: RewritingData):
        if data.index == 0:
            name = "CERTAINTY"
        else:
            name = "RewriteAtom_" + str(data.index)
        if data.index == 0 and len(data.frozen) == 0:
            content = []
        else:
            content = data.frozen
        head = Atom(name, content)
        FORewritingQuery.__init__(self, head, data.done)
        self.add_atom(data.atom)
        if data.has_c or not data.is_last:
            self.add_atom(Atom("BadBlock_" + str(data.index), data.frozen + data.vars_x), True)
        self.make_safe(data.q)


class BadBlockQuery(FORewritingQuery):
    def __init__(self, data: RewritingData):
        head = Atom("BadBlock_" + str(data.index), data.frozen + data.vars_x)
        head.released = set(data.frozen + data.vars_x)
        FORewritingQuery.__init__(self, head, data.done)
        z_atom = Atom(data.atom.name, data.x + data.vars_z)
        z_atom.released = set(data.frozen + data.vars_x).intersection(set(z_atom.content))
        self.add_atom(z_atom)
        if data.has_c:
            self.add_atom(Atom("GoodFact_" + str(data.index), data.frozen + data.vars_x + data.vars_z), True)
        else:
            self.add_atom(Atom("RewriteAtom_" + str(data.index + 1), data.new_frozen), True)
        self.make_safe(data.q)


class GoodFactQuery(FORewritingQuery):
    def __init__(self, data: RewritingData):
        head = Atom("GoodFact_" + str(data.index), data.frozen + data.vars_x + data.vars_z)
        head.released = set(data.frozen + data.vars_x + data.vars_z)
        FORewritingQuery.__init__(self, head, data.done)
        z_atom = Atom(data.atom.name, data.x + data.vars_z)
        z_atom.released = set(data.frozen + data.vars_x + data.vars_z).intersection(set(z_atom.content))
        self.add_atom(z_atom)
        for val in data.c:
            ea = EqualityAtom(val, data.c[val])
            ea.released = set(data.frozen + data.vars_x + data.vars_z).intersection({val, data.c[val]})
            self.add_atom(ea)
        if not data.is_last:
            self.add_atom(Atom("RewriteAtom_" + str(data.index + 1), data.new_frozen))
        self.make_safe(data.q)


class EqQuery(DatalogQuery):
    def __init__(self, atom, q):
        _, x, _ = q.decompose_atom(atom)
        head_atom = Atom("Eq_" + atom.name, x * 2)
        DatalogQuery.__init__(self, head_atom)
        self.add_atom(atom)


class NeqQuery(DatalogQuery):
    def __init__(self, atom, q, renaming):
        v, x, _ = q.decompose_atom(atom)
        renamed_x = apply_renaming_to_atom_values(x, renaming)
        head_atom = Atom("Neq_" + atom.name, x + renamed_x)
        renamed_atom = apply_renaming_to_atom(atom, renaming)
        eq_atom = Atom("Eq_" + atom.name, x + renamed_x)
        DatalogQuery.__init__(self, head_atom)
        self.add_atom(atom)
        self.add_atom(renamed_atom)
        self.add_atom(eq_atom, True)


class RelevantQuery(DatalogQuery):
    def __init__(self, atom, q):
        head_atom = Atom("Rlvant_" + atom.name, atom.content)
        DatalogQuery.__init__(self, head_atom)
        for atom2 in q.get_atoms():
            self.add_atom(atom2)


class GarbageRelevantQuery(DatalogQuery):
    def __init__(self, atom, q):
        _, x, _ = q.decompose_atom(atom)
        head_atom = Atom("Garbage_" + atom.name, x)
        relevant_atom = Atom("Rlvant_" + atom.name, atom.content)
        DatalogQuery.__init__(self, head_atom)
        self.add_atom(atom)
        self.add_atom(relevant_atom, True)


class Any1EmbQuery(DatalogQuery):
    def __init__(self, cycle, q, rewriting_index, renamings):
        k = len(cycle)
        head_content = []
        for i in range(k):
            _, x, y = q.decompose_atom(cycle[i])
            head_content += apply_renaming_to_atom_values(x, renamings[i])
            head_content += apply_renaming_to_atom_values(y, renamings[i])
        head_atom = Atom("Any1Emb_" + str(rewriting_index), head_content)
        DatalogQuery.__init__(self, head_atom)
        for i in range(k):
            for atom in q.get_atoms():
                self.add_atom(apply_renaming_to_atom(atom, renamings[i]))
        for i in range(k):
            _, x, y = q.decompose_atom(cycle[i])
            key1 = apply_renaming_to_atom_values(x, renamings[i])
            key2 = apply_renaming_to_atom_values(x, renamings[(k - 1 + i) % k])
            self.add_atom(Atom("Eq_" + cycle[i].name, key1 + key2))


class Rel1EmbQuery(DatalogQuery):
    def __init__(self, cycle, q, rewriting_index):
        head_content = []
        for atom in cycle:
            _, x, y = q.decompose_atom(atom)
            head_content += x
            head_content += y
        head_atom = Atom("Rel1Emb_" + str(rewriting_index), head_content)
        DatalogQuery.__init__(self, head_atom)
        for atom in cycle:
            self.add_atom(atom)


class Irr1EmbQuery(DatalogQuery):
    def __init__(self, cycle, q, rewriting_index, renamings):
        k = len(cycle)
        head_content = []
        any_content = []
        for i in range(k):
            _, x, y = q.decompose_atom(cycle[i])
            head_content += apply_renaming_to_atom_values(x, renamings[i])
            any_content += apply_renaming_to_atom_values(x, renamings[i])
            any_content += apply_renaming_to_atom_values(y, renamings[i])
        head_atom = Atom("Irr1Emb_" + str(rewriting_index), head_content)
        DatalogQuery.__init__(self, head_atom)
        self.add_atom(Atom("Any1Emb_" + str(rewriting_index), any_content))
        self.add_atom(Atom("Rel1Emb_" + str(rewriting_index), any_content), True)


class Garbage1EmbQuery(DatalogQuery):
    def __init__(self, atom, cycle, q, rewriting_index, renamings):
        index = cycle.index(atom)
        k = len(cycle)
        _, x, _ = q.decompose_atom(atom)
        head_atom = Atom("Garbage_" + atom.name, apply_renaming_to_atom_values(x, renamings[index]))
        DatalogQuery.__init__(self, head_atom)
        irr_content = []
        for i in range(k):
            _, x, _ = q.decompose_atom(cycle[i])
            irr_content += apply_renaming_to_atom_values(x, renamings[i])
        self.add_atom(Atom("Irr1Emb_" + str(rewriting_index), irr_content))


class PkQuery(DatalogQuery):
    def __init__(self, cycle, q, rewriting_index, renamings):
        k = len(cycle)
        head_content = []
        for i in range(k):
            _, x, _ = q.decompose_atom(cycle[i])
            head_content += apply_renaming_to_atom_values(x, renamings[i])
        _, x_0, _ = q.decompose_atom(cycle[0])
        x_0_k = apply_renaming_to_atom_values(x_0, renamings[k])
        head_content += x_0_k
        head_atom = Atom("Pk_" + str(rewriting_index), head_content)
        DatalogQuery.__init__(self, head_atom)
        for i in range(k + 1):
            for atom in q.get_atoms():
                self.add_atom(apply_renaming_to_atom(atom, renamings[i]))
        for i in range(1, k):
            _, x, y = q.decompose_atom(cycle[i])
            key1 = apply_renaming_to_atom_values(x, renamings[i])
            key2 = apply_renaming_to_atom_values(x, renamings[i - 1])
            self.add_atom(Atom("Eq_" + cycle[i].name, key1 + key2))
        x_0_k_1 = apply_renaming_to_atom_values(x_0, renamings[k - 1])
        x_0_0 = apply_renaming_to_atom_values(x_0, renamings[0])
        self.add_atom(Atom("Eq_" + cycle[0].name, x_0_k + x_0_k_1))
        self.add_atom(Atom("Neq_" + cycle[0].name, x_0_0 + x_0_k))


class DConRecQuery(DatalogQuery):
    def __init__(self, cycle, q, rewriting_index, renamings):
        k = len(cycle)
        head_content = []
        _, x_0, _ = q.decompose_atom(cycle[0])
        x_0_0 = apply_renaming_to_atom_values(x_0, renamings[0])
        x_0_2k = apply_renaming_to_atom_values(x_0, renamings[2 * k])
        head_content += x_0_0
        head_content += x_0_2k
        common = []
        for i in range(1, k):
            _, x, _ = q.decompose_atom(cycle[i])
            common += apply_renaming_to_atom_values(x, renamings[i])
        head_atom = Atom("DCon_" + str(rewriting_index), head_content + common)
        DatalogQuery.__init__(self, head_atom)
        x_0_2k_1 = apply_renaming_to_atom_values(x_0, renamings[2 * k + 1])
        self.add_atom(Atom("DCon_" + str(rewriting_index), x_0_0 + x_0_2k_1 + common))
        pk_content = x_0_2k_1
        for i in range(1, k):
            _, x, _ = q.decompose_atom(cycle[i])
            pk_content += apply_renaming_to_atom_values(x, renamings[k + i])
        pk_content += x_0_2k
        self.add_atom(Atom("Pk_" + str(rewriting_index), pk_content))
        for i in range(1, k):
            _, x, _ = q.decompose_atom(cycle[i])
            key1 = apply_renaming_to_atom_values(x, renamings[k + i])
            key2 = apply_renaming_to_atom_values(x, renamings[i])
            self.add_atom(Atom("Neq_" + cycle[i].name, key1 + key2))


class DConBaseQuery(DatalogQuery):
    def __init__(self, cycle, q, rewriting_index, renamings):
        k = len(cycle)
        head_content = []
        _, x_0, _ = q.decompose_atom(cycle[0])
        x_0_2k = apply_renaming_to_atom_values(x_0, renamings[2 * k])
        head_content += x_0_2k * 2
        common = []
        for i in range(1, k):
            _, x, _ = q.decompose_atom(cycle[i])
            common += apply_renaming_to_atom_values(x, renamings[i])
        head_atom = Atom("DCon_" + str(rewriting_index), head_content + common)
        DatalogQuery.__init__(self, head_atom)
        for atom in cycle:
            self.add_atom(apply_renaming_to_atom(atom, renamings[2 * k]))
        x_0_0 = apply_renaming_to_atom_values(x_0, renamings[0])
        x_0_k = apply_renaming_to_atom_values(x_0, renamings[k])
        self.add_atom(Atom("Pk_" + str(rewriting_index), x_0_0 + common + x_0_k))


class InLongDCycleQuery(DatalogQuery):
    def __init__(self, cycle, q, rewriting_index, renamings):
        k = len(cycle)
        head_content = []
        for i in range(k):
            _, x, _ = q.decompose_atom(cycle[i])
            head_content += apply_renaming_to_atom_values(x, renamings[i])
        head_atom = Atom("InLongDCycle_" + str(rewriting_index), head_content)
        DatalogQuery.__init__(self, head_atom)
        _, x_0, _ = q.decompose_atom(cycle[0])
        x_0_k = apply_renaming_to_atom_values(x_0, renamings[k])
        self.add_atom(Atom("Pk_" + str(rewriting_index), head_content + x_0_k))
        self.add_atom(Atom("DCon_" + str(rewriting_index), x_0_k + head_content))


class GarbageLongCycleQuery(DatalogQuery):
    def __init__(self, atom, cycle, q, rewriting_index):
        _, x, y = q.decompose_atom(atom)
        head_atom = Atom("Garbage_" + atom.name, x)
        DatalogQuery.__init__(self, head_atom)
        cycle_content = []
        for other in cycle:
            _, x, y = q.decompose_atom(other)
            cycle_content += x
        self.add_atom(Atom("InLongDCycle_" + str(rewriting_index), cycle_content))


class GarbagePropagateQuery(DatalogQuery):
    def __init__(self, atom1, atom2, q):
        _, x1, _ = q.decompose_atom(atom1)
        _, x2, _ = q.decompose_atom(atom2)
        head_atom = Atom("Garbage_" + atom1.name, x1)
        DatalogQuery.__init__(self, head_atom)
        for atom in q.get_atoms():
            self.add_atom(atom)
        self.add_atom(Atom("Garbage_" + atom2.name, x2))


class KeepQuery(DatalogQuery):
    def __init__(self, atom, q):
        _, x, y = q.decompose_atom(atom)
        head_atom = Atom("Keep_" + atom.name, x + y)
        DatalogQuery.__init__(self, head_atom)
        self.add_atom(atom)
        self.add_atom(Atom("Garbage_" + atom.name, x), True)


class LinkQuery(DatalogQuery):
    def __init__(self, atom, cycle, q, rewriting_index, renaming):
        k = len(cycle)
        _, x_0, _ = q.decompose_atom(cycle[0])
        x_0_ren = apply_renaming_to_atom_values(x_0, renaming)
        DatalogQuery.__init__(self, Atom("Link_" + str(rewriting_index), x_0 + x_0_ren))
        for i in range(k):
            _, x, y = q.decompose_atom(cycle[i])
            self.add_atom(Atom("Keep_" + cycle[i].name, x + y))
            x = apply_renaming_to_atom_values(x, renaming)
            y = apply_renaming_to_atom_values(y, renaming)
            self.add_atom(Atom("Keep_" + cycle[i].name, x + y))
        index = cycle.index(atom)
        _, x_i, _ = q.decompose_atom(cycle[index])
        x_i_ren = apply_renaming_to_atom_values(x_i, renaming)
        self.add_atom(Atom("Eq_" + atom.name, x_i + x_i_ren))


class TransBaseQuery(DatalogQuery):
    def __init__(self, cycle, q, rewriting_index, renaming):
        _, x_0, _ = q.decompose_atom(cycle[0])
        x_0_ren = apply_renaming_to_atom_values(x_0, renaming)
        DatalogQuery.__init__(self, Atom("Trans_" + str(rewriting_index), x_0 + x_0_ren))
        self.add_atom(Atom("Link_" + str(rewriting_index), x_0 + x_0_ren))


class TransRecQuery(DatalogQuery):
    def __init__(self, cycle, q, rewriting_index, renamings):
        _, x_0, _ = q.decompose_atom(cycle[0])
        x_0_0 = apply_renaming_to_atom_values(x_0, renamings[0])
        x_0_1 = apply_renaming_to_atom_values(x_0, renamings[1])
        DatalogQuery.__init__(self, Atom("Trans_" + str(rewriting_index), x_0 + x_0_0))
        self.add_atom(Atom("Trans_" + str(rewriting_index), x_0 + x_0_1))
        self.add_atom(Atom("Link_" + str(rewriting_index), x_0_1 + x_0_0))


class LowerSingleQuery(DatalogQuery):
    def __init__(self, cycle, q, rewriting_index, renamings):
        _, x_0, _ = q.decompose_atom(cycle[0])
        x_0_0 = apply_renaming_to_atom_values(x_0, renamings[0])[0]
        x_0_1 = apply_renaming_to_atom_values(x_0, renamings[1])[0]
        x_0 = x_0[0]
        DatalogQuery.__init__(self, Atom("Lower_" + str(rewriting_index), [x_0, x_0_0]))
        self.add_atom(Atom("Trans_" + str(rewriting_index), [x_0, x_0_0]))
        self.add_atom(Atom("Trans_" + str(rewriting_index), [x_0, x_0_1]))
        self.add_atom(CompareAtom(x_0_0, x_0_1, True))


class LowerCompositeQuery(DatalogQuery):
    def __init__(self, cycle, q, index, rewriting_index, renamings):
        _, x_0, _ = q.decompose_atom(cycle[0])
        x_0_0 = apply_renaming_to_atom_values(x_0, renamings[0])
        x_0_1 = apply_renaming_to_atom_values(x_0, renamings[1])
        DatalogQuery.__init__(self, Atom("Lower_" + str(rewriting_index), x_0 + x_0_0))
        self.add_atom(Atom("Trans_" + str(rewriting_index), x_0 + x_0_0))
        self.add_atom(Atom("Trans_" + str(rewriting_index), x_0 + x_0_1))
        for i in range(0, index - 1):
            self.add_atom(EqualityAtom(x_0_0[i], x_0_1[i]))
        self.add_atom(CompareAtom(x_0_0[index], x_0_1[index], True))


class IdentifiedByQuery(DatalogQuery):
    def __init__(self, cycle, q, rewriting_index, renaming):
        _, x_0, _ = q.decompose_atom(cycle[0])
        x_0_ren = apply_renaming_to_atom_values(x_0, renaming)
        DatalogQuery.__init__(self, Atom("IdentifiedBy_" + str(rewriting_index), x_0 + x_0_ren))
        self.add_atom(Atom("Lower_" + str(rewriting_index), x_0 + x_0_ren), True)
        self.add_atom(Atom("Trans_" + str(rewriting_index), x_0 + x_0_ren))


class TQuery(DatalogQuery):
    def __init__(self, cycle, q, rewriting_index, renaming):
        _, x_0, _ = q.decompose_atom(cycle[0])
        x_0_ren = apply_renaming_to_atom_values(x_0, renaming)
        head_content = []
        body_atoms = []
        head_content += x_0_ren
        for atom in cycle:
            _, x, y = q.decompose_atom(atom)
            head_content += x + y
            body_atoms.append(Atom("Keep_" + atom.name, x + y))
        DatalogQuery.__init__(self, Atom("T_" + str(rewriting_index), head_content))
        for atom in body_atoms:
            self.add_atom(atom)
        self.add_atom(Atom("IdentifiedBy_" + str(rewriting_index), x_0 + x_0_ren))


class NQuery(DatalogQuery):
    def __init__(self, atom, cycle, q, rewriting_index, renaming):
        _, x, _ = q.decompose_atom(atom)
        _, x_0, _ = q.decompose_atom(cycle[0])
        x_0_ren = apply_renaming_to_atom_values(x_0, renaming)
        DatalogQuery.__init__(self, Atom("N_" + atom.name, x + x_0_ren))
        t_atom_content = x_0_ren
        for atom in cycle:
            _, x, y = q.decompose_atom(atom)
            t_atom_content += x
            t_atom_content += y
        self.add_atom(Atom("T_" + str(rewriting_index), t_atom_content))
