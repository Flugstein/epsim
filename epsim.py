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
        self.school_nbrs = []
        self.office_nbrs = {}


    def init_from_dicts(self, family_nbrs, school_nbrs, office_nbrs):
        self.family_nbrs = family_nbrs
        self.school_nbrs = school_nbrs
        self.office_nbrs = office_nbrs
        self.node_states = {node: 0 for (node, nbrs) in family_nbrs.items()}


    def init_from_files(self, family_nbrs_path, school_nbrs_path, office_nbrs_path, split_classes):
        print('read nbrs files')
        self.read_nbrs_file(self.family_nbrs, family_nbrs_path)
        self.read_nbrs_file(self.office_nbrs, office_nbrs_path)
        self.node_states = {node: 0 for (node, nbrs) in self.family_nbrs.items()}

        files = "_0 _1".split() if split_classes else {"_0"}
        for f in files: 
            cur = {}
            self.read_nbrs_file(cur, school_nbrs_path + f)
            self.school_nbrs.append(cur)


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
                f.write('{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10}\n'.format(
                    rnd, states[0], states[1], states[2], states[3], states[4], states[5],
                    info['infec_family'], info['infec_school'], info['infec_office'], info['immunized']))


    def immunize_node(self, node):
        self.node_states[node] = 5
        if node in self.infec_nodes:
            self.infec_nodes.remove(node)
        if node in self.spreading_child_nodes:
            self.spreading_child_nodes.remove(node)
        if node in self.spreading_parent_nodes:
            self.spreading_parent_nodes.remove(node)


    def spread(self, nbrs_dict, spreading_nodes, prob):
        infec_nodes = []
        for spreading_node in spreading_nodes:
            if spreading_node in nbrs_dict:
                for nbr in nbrs_dict[spreading_node]:
                    if self.node_states[nbr] == 0:
                        if random.random() < prob:
                            self.node_states[nbr] = 1
                            infec_nodes.append(nbr)
        return infec_nodes


    def immunize_family_nbrs(self, nodes, prob):
        immunized_nodes = []
        for node in nodes:
            if random.random() < prob:
                for nbr in self.family_nbrs[node]:
                    self.immunize_node(nbr)
                    immunized_nodes.append(nbr)
        return immunized_nodes


    def immunize_after_testing(self, spreading_nodes, prob):
        pos_tested_nodes = []
        for spreading_node in spreading_nodes:
            if random.random() < prob:
                self.immunize_node(spreading_node)
                pos_tested_nodes.append(spreading_node)
        return pos_tested_nodes


    def run_sim(self, sim_iters, family_spread_prob, school_office_spread_prob, detect_prob, testing_prob, print_progress=False, export_csv=False):
        num_start_nodes = int(2*math.log(len(self.node_states)))
        start_nodes = random.sample(self.node_states.keys(), num_start_nodes)
        for node in self.node_states:
            self.node_states[node] = 0
        for node in start_nodes:
            self.node_states[node] = 1

        print('starting simulation with n={}, num_start_nodes={}, sim_iters={}'.format(
            len(self.node_states), len(start_nodes), sim_iters))
        print('family_spread_prob={}, school_office_spread_prob={}, detect_prob={}, testing_prob={}'.format(
            family_spread_prob, school_office_spread_prob, detect_prob, testing_prob))
        x_rounds = []
        y_num_infec = []
        states_per_rnd = []
        info_per_rnd = []

        for rnd in range(sim_iters):
            weekday = rnd % 7
            self.infec_nodes = [node for node, state in self.node_states.items() if state in [1, 2, 3, 4]]
            self.spreading_parent_nodes = [node for node, state in self.node_states.items() if state in [3, 4] and node in self.office_nbrs]
            self.spreading_child_nodes = [node for node, state in self.node_states.items() if state in [3, 4] and node not in self.office_nbrs]

            # spread in family every day
            infec_family_nodes = self.spread(self.family_nbrs, self.spreading_parent_nodes + self.spreading_child_nodes, family_spread_prob)

            # children are tested on monday morning and if they test positive, them and their families get quarantined
            if weekday == 0:
                pos_tested_child_nodes = self.immunize_after_testing(self.spreading_child_nodes, testing_prob)
                immunized_family_nbrs = self.immunize_family_nbrs(pos_tested_child_nodes, prob=1.0)
                immunized_by_monday_test = pos_tested_child_nodes + immunized_family_nbrs

            # spread in office and school only during weekdays
            if weekday in [0, 1, 2, 3, 4]:
                # spread in office
                infec_office_parent_nodes = self.spread(self.office_nbrs, self.spreading_parent_nodes, school_office_spread_prob)
                # school classes are split and rotate every day
                current_class = rnd % len(self.school_nbrs)
                infec_school_child_nodes = self.spread(self.school_nbrs[current_class], self.spreading_child_nodes, school_office_spread_prob)
                # with detect_prob an infection of a child gets detected (shows symtoms) and its family gets quarantined
                immunized_by_detection = self.immunize_family_nbrs(infec_school_child_nodes, detect_prob)

            # all infected nodes increase their state every round
            for infec_node in self.infec_nodes:
                self.node_states[infec_node] += 1

            # info tracking
            states_per_rnd.append([0] * num_node_states)
            for state in self.node_states.values():
                states_per_rnd[rnd][state] += 1
            info_per_rnd.append({
                'infec_family': len(infec_family_nodes),
                'infec_school': len(infec_school_child_nodes),
                'infec_office': len(infec_office_parent_nodes),
                'immunized': len(immunized_by_monday_test) + len(immunized_by_detection)})
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
    if len(sys.argv) != 12:
        print('usage: python epsim.py sim_iters family_spread_prob school_office_spread_prob detect_prob \
                testing_prob split_classes family.nbrs school.nbrs office.nbrs out.csv')
        quit()

    sim_iters = int(sys.argv[1])
    family_spread_prob = float(sys.argv[2])
    school_office_spread_prob = float(sys.argv[3])
    detect_prob = float(sys.argv[4])
    testing_prob = float(sys.argv[5])
    split_classes = sys.argv[6] == 'true'
    family_nbrs_path = sys.argv[7]
    school_nbrs_path = sys.argv[8]
    office_nbrs_path = sys.argv[9]
    out_path = sys.argv[10]

    epsim = Epsim()
    epsim.init_from_files(family_nbrs_path, school_nbrs_path, office_nbrs_path, split_classes)
    x_rounds, y_num_infec = epsim.run_sim(sim_iters, family_spread_prob, school_office_spread_prob,
                                          detect_prob, testing_prob)

    with open(out_path, 'w') as f:
        for i in range(len(x_rounds)):
            f.write('{}, {}\n'.format(x_rounds[i], y_num_infec[i]))
