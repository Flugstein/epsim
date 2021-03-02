import sys
import numpy as np
import random
import math
import time

### node states ###
# 0 not infected
# 1 infected: incubation
# 2 infected: incubation
# 3 infected: spreading
# 4 infected: spreading
# 5 immune
num_node_states = 6

class Epsim:
    def __init__(self):
        self.node_states = {}
        self.family_nbrs = {}
        self.school_nbrs_standard = {}
        self.school_nbrs_split = [{}, {}]
        self.office_nbrs = {}


    def init_from_dicts(self, family_nbrs, school_nbrs_standard, school_nbrs_split, office_nbrs):
        self.family_nbrs = family_nbrs
        self.school_nbrs_standard = school_nbrs_standard
        self.school_nbrs_split = school_nbrs_split
        self.office_nbrs = office_nbrs
        self.node_states = {node: 0 for (node, nbrs) in family_nbrs.items()}


    def init_from_files(self, family_nbrs_path, school_standard_path, school_split_0_path, school_split_1_path, office_nbrs_path):
        print('read nbrs files')
        self.read_nbrs_file(self.family_nbrs, family_nbrs_path)
        self.read_nbrs_file(self.office_nbrs, office_nbrs_path)
        self.node_states = {node: 0 for (node, nbrs) in self.family_nbrs.items()}

        if school_standard_path:
            self.read_nbrs_file(self.school_nbrs_standard, school_standard_path)
        if school_split_0_path:
            self.school_nbrs_split = []
            for p in (school_split_0_path, school_split_1_path):
                cur = {}
                self.read_nbrs_file(cur, p)
                self.school_nbrs_split.append(cur)


    def read_nbrs_file(self, nbrs_dict, nbrs_file_path):
        with open(nbrs_file_path) as f:
            for line in f:
                node, nbrs = line.split(':')
                node = int(node)
                nbrs = set(map(int, nbrs.split()))
                nbrs_dict[node] = nbrs


    def write_csv(self, file_path, states_per_rnd, info_per_rnd):
        with open(file_path, 'w') as f:
            f.write('round,state_0,state_1,state_2,state_3,state_4,state_5,infec_family,infec_school,infec_office,immunized\n')
            for rnd, states in enumerate(states_per_rnd):
                info = info_per_rnd[rnd]
                f.write('{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11}\n'.format(
                    rnd, states[0], states[1], states[2], states[3], states[4], states[5],
                    info['infec_family'], info['infec_school'], info['infec_office'], info['immunized_detect'], info['immunized_test']))


    def immunize_node(self, node):
        self.node_states[node] = 5
        self.infec_nodes.discard(node)
        self.spreading_parent_nodes.discard(node)
        self.spreading_child_nodes.discard(node)
        self.spreading_child_nodes_standard.discard(node)


    def spread(self, nbrs_dict, spreading_nodes, prob):
        infec_nodes = set()
        for spreading_node in spreading_nodes:
            if spreading_node in nbrs_dict:
                for nbr in nbrs_dict[spreading_node]:
                    if self.node_states[nbr] == 0:
                        if random.random() < prob:
                            self.node_states[nbr] = 1
                            infec_nodes.add(nbr)
        return infec_nodes


    def immunize_family_nbrs(self, nodes, prob):
        immunized_nodes = set()
        for node in nodes:
            if random.random() < prob:
                for nbr in self.family_nbrs[node]:
                    self.immunize_node(nbr)
                    immunized_nodes.add(nbr)
        return immunized_nodes


    def immunize_after_testing(self, spreading_nodes, prob):
        pos_tested_nodes = set()
        for spreading_node in spreading_nodes:
            if random.random() < prob:
                pos_tested_nodes.add(spreading_node)
        for node in pos_tested_nodes:
            self.immunize_node(node)
        return pos_tested_nodes


    def run_sim(self, sim_iters, p_spread_family, p_spread_school_office, p_detect_child, p_detect_parent, p_testing, print_progress=False, export_csv=False):
        num_start_nodes = int(2*math.log(len(self.node_states)))
        start_nodes = random.sample(self.node_states.keys(), num_start_nodes)
        for node in self.node_states:
            self.node_states[node] = 0
        for node in start_nodes:
            self.node_states[node] = 1

        print('starting simulation with n={}, num_start_nodes={}, sim_iters={}'.\
            format(len(self.node_states), len(start_nodes), sim_iters))
        print('p_spread_family={}, p_spread_school_office={}, p_detect_child={}, p_detect_parent={} p_testing={}'.\
            format(p_spread_family, p_spread_school_office, p_detect_child, p_detect_parent, p_testing))
        print(f"{len(self.school_nbrs_split[0]) + len(self.school_nbrs_split[1])} children in split classes and {len(self.school_nbrs_standard)} children in standard classes")
        x_rounds = []
        y_num_infec = []
        states_per_rnd = []
        info_per_rnd = []

        for rnd in range(sim_iters):
            weekday = rnd % 7
            self.infec_nodes = {node for node, state in self.node_states.items() if state in [1, 2, 3, 4]}
            self.spreading_parent_nodes = {node for node, state in self.node_states.items() if state in [3, 4] and node in self.office_nbrs}
            self.spreading_child_nodes = {node for node, state in self.node_states.items() if state in [3, 4] and node not in self.office_nbrs}
            self.spreading_child_nodes_standard = {node for node in self.spreading_child_nodes if node in self.school_nbrs_standard}

            # spread in family every day
            infec_family = self.spread(self.family_nbrs, self.spreading_parent_nodes.union(self.spreading_child_nodes), p_spread_family)

            # children are tested on monday morning and if they test positive, them and their families get quarantined
            immunized_monday_test = set()
            if weekday == 0:
                pos_tested_child_nodes = self.immunize_after_testing(self.spreading_child_nodes, p_testing)
                immunized_family_nbrs = self.immunize_family_nbrs(pos_tested_child_nodes, prob=1.0)
                immunized_monday_test = pos_tested_child_nodes.union(immunized_family_nbrs)

            # on wednesday children in non-split classes get tested
            immunized_wednesday_test = set()
            if weekday == 2:
                pos_tested_child_nodes = self.immunize_after_testing(self.spreading_child_nodes_standard, p_testing)
                immunized_family_nbrs = self.immunize_family_nbrs(pos_tested_child_nodes, prob=1.0)
                immunized_wednesday_test = pos_tested_child_nodes.union(immunized_family_nbrs) 

            # spread in office and school only during weekdays
            infec_office = set()
            infec_school_standard = set()
            infec_school_split = set()
            immunized_detect_standard = set()
            immunized_detect_split = set()
            if weekday in [0, 1, 2, 3, 4]:
                # spread in office
                infec_office = self.spread(self.office_nbrs, self.spreading_parent_nodes, p_spread_school_office)
                # with p_detect_parent an infection of a parent gets detected (shows symtoms) and its family gets quarantined
                immunized_detect_office = self.immunize_family_nbrs(infec_office, p_detect_parent)

                # handle standard classes
                if len(self.school_nbrs_standard) > 0:
                    infec_school_standard = self.spread(self.school_nbrs_standard, self.spreading_child_nodes, p_spread_school_office)
                    # with p_detect_child an infection of a child gets detected (shows symtoms) and its family gets quarantined
                    immunized_detect_standard = self.immunize_family_nbrs(infec_school_standard, p_detect_child)

                # handle alternating split classes
                if len(self.school_nbrs_split[0]) > 0:
                    current_class = rnd % 2
                    infec_school_split = self.spread(self.school_nbrs_split[current_class], self.spreading_child_nodes, p_spread_school_office)
                    immunized_detect_split = self.immunize_family_nbrs(infec_school_split, p_detect_child)

            # all infected nodes increase their state every round
            for infec_node in self.infec_nodes:
                self.node_states[infec_node] += 1

            # info tracking
            states_per_rnd.append([0] * num_node_states)
            for state in self.node_states.values():
                states_per_rnd[rnd][state] += 1
            info_per_rnd.append({
                'infec_family': len(infec_family),
                'infec_school': len(infec_school_standard) + len(infec_school_split),
                'infec_office': len(infec_office),
                'immunized_detect': len(immunized_detect_office) + len(immunized_detect_standard) + len(immunized_detect_split),
                'immunized_test': len(immunized_monday_test) + len(immunized_wednesday_test)})
            if print_progress:
                print('{}:\t{}\t{}'.format(rnd, states_per_rnd[rnd], list(info_per_rnd[rnd].values())))
            if export_csv:
                self.write_csv(export_csv, states_per_rnd, info_per_rnd)

            num_infec = sum(states_per_rnd[rnd][1:])
            x_rounds.append(rnd)
            y_num_infec.append(num_infec)

        print('infected nodes: {}\n'.format(num_infec))
        return x_rounds, y_num_infec


if __name__ == '__main__':
    if not (10 <= len(sys.argv) <= 12):
        print('usage: python epsim.py sim_iters p_spread_family p_spread_school_office p_detect_child p_detect_parent \
                p_testing family.nbrs office.nbrs out.csv [school_standard.nbrs] [school_split_0.nbrs school_split_1.nbrs]')
        print('specify either school_standard.nbrs or school_split.nbrs, or both')
        print('children in school_standard.nbrs visit school every day. children in school_split.nbrs visit school every other day, alternating.')
        quit()

    sim_iters = int(sys.argv[1])
    p_spread_family = float(sys.argv[2])
    p_spread_school_office = float(sys.argv[3])
    p_detect_child = float(sys.argv[4])
    p_detect_parent = float(sys.argv[5])
    p_testing = float(sys.argv[6])
    family_nbrs_path = sys.argv[7]
    office_nbrs_path = sys.argv[8]
    out_path = sys.argv[9]

    school_standard = None
    school_split_0 = None
    school_split_1 = None

    if len(sys.argv) == 11:
        school_standard = sys.argv[10]
    elif len(sys.argv) == 12:
        school_split_0 = sys.argv[10]
        school_split_1 = sys.argv[11]
    else:
        school_standard = sys.argv[10]
        school_split_0 = sys.argv[11]
        school_split_1 = sys.argv[12]

    epsim = Epsim()
    epsim.init_from_files(family_nbrs_path, school_standard, school_split_0, school_split_1, office_nbrs_path)
    x_rounds, y_num_infec = epsim.run_sim(sim_iters, p_spread_family, p_spread_school_office,
                                          p_detect_child, p_detect_parent, p_testing)

    with open(out_path, 'w') as f:
        for i in range(len(x_rounds)):
            f.write('{}, {}\n'.format(x_rounds[i], y_num_infec[i]))
