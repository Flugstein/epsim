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


    def immunize_node(self, node):
        self.node_states[node] = 5
        if node in self.inf_nodes:
            self.inf_nodes.remove(node)
        if node in self.spreading_child_nodes:
            self.spreading_child_nodes.remove(node)
        if node in self.spreading_parent_nodes:
            self.spreading_parent_nodes.remove(node)


    def spread(self, nbrs_dict, spreading_nodes, prob):
        for spreading_node in spreading_nodes:
            if spreading_node in nbrs_dict:
                for nbr in nbrs_dict[spreading_node]:
                    if self.node_states[nbr] == 0:
                        if random.random() < prob:
                            self.node_states[nbr] = 1


    def spread_ret(self, nbrs_dict, spreading_nodes, prob):
        infec_nodes = []
        for spreading_node in spreading_nodes:
            if spreading_node in nbrs_dict:
                for nbr in nbrs_dict[spreading_node]:
                    if self.node_states[nbr] == 0:
                        if random.random() < prob:
                            self.node_states[nbr] = 1
                            infec_nodes.append(nbr)
        return infec_nodes


    def immunize_child_family_nbrs(self, infec_child_nodes, prob):
        for infec_child_node in infec_child_nodes:
            if random.random() < prob:
                for nbr in self.family_nbrs[infec_child_node]:
                    self.immunize_node(nbr)


    def immunize_children_after_testing(self, spreading_child_nodes, prob):
        positive_tested_child_nodes = []
        for spreading_child_node in spreading_child_nodes:
            if random.random() < prob:
                self.immunize_node(spreading_child_node)
                positive_tested_child_nodes.append(spreading_child_node)
        return positive_tested_child_nodes


    # similar to immunize_child_family_nbrs
    def quarantine_family(self, positive_tested_child_nodes, prob):
        for child_node in positive_tested_child_nodes:
            if random.random() < prob:
                for nbr in self.family_nbrs[child_node]:
                    self.immunize_node(nbr)


    def run_sim(self, sim_iters, family_spread_prob, school_office_spread_prob, immunize_prob, testing_prob, quarantine_prob, print_progress=False):
        num_start_nodes = int(2*math.log(len(self.node_states)))
        start_nodes = random.sample(self.node_states.keys(), num_start_nodes)
        for node in self.node_states:
            self.node_states[node] = 0
        for node in start_nodes:
            self.node_states[node] = 1

        print('starting simulation with n={}, num_start_nodes={}, sim_iters={}'.\
            format(len(self.node_states), len(start_nodes), sim_iters))
        print('family_spread_prob={}, school_office_spread_prob={}, immunize_prob={}, testing_prob={}, quarantine_prob={}'.\
            format(family_spread_prob, school_office_spread_prob, immunize_prob, testing_prob, quarantine_prob))
        x_rounds = []
        y_num_infected = []
        states_per_rnd = []

        for rnd in range(sim_iters):
            weekday = rnd % 7
            self.inf_nodes = [node for node, state in self.node_states.items() if state in [1, 2, 3, 4]]
            self.spreading_parent_nodes = [node for node, state in self.node_states.items() if state in [3, 4] and node in self.office_nbrs]
            self.spreading_child_nodes = [node for node, state in self.node_states.items() if state in [3, 4] and node not in self.office_nbrs]

            # spread in family every day
            self.spread(self.family_nbrs, self.spreading_parent_nodes + self.spreading_child_nodes, family_spread_prob)

            # children are tested on monday morning and if they test positive, their family gets quarantined
            if weekday == 0:
                positive_tested_child_nodes = self.immunize_children_after_testing(self.spreading_child_nodes, testing_prob)
                self.quarantine_family(positive_tested_child_nodes, quarantine_prob)

            # spread in office and school only during weekdays
            if weekday in [0, 1, 2, 3, 4]:
                # spread in office
                self.spread(self.office_nbrs, self.spreading_parent_nodes, school_office_spread_prob)
                # school classes are split and rotate every day
                current_class = rnd % len(self.school_nbrs)
                infec_child_nodes = self.spread_ret(self.school_nbrs[current_class], self.spreading_child_nodes, school_office_spread_prob)
                # with immunize_prob the family of a just infected child becomes immune
                self.immunize_child_family_nbrs(infec_child_nodes, immunize_prob)

            states_per_rnd.append([0] * num_node_states)
            for state in self.node_states.values():
                states_per_rnd[rnd][state] += 1
            if print_progress:
                print(str(rnd) + ': ' + str(states_per_rnd[rnd]))

            num_infeced = sum(states_per_rnd[rnd][1:])
            x_rounds.append(rnd)
            y_num_infected.append(num_infeced)

            # all infected nodes increase their state every round
            for inf_node in self.inf_nodes:
                self.node_states[inf_node] += 1

        print('infected nodes: {}\n'.format(num_infeced))
        return x_rounds, y_num_infected


if __name__ == '__main__':
    if len(sys.argv) != 12:
        print('usage: python epsim.py sim_iters family_spread_prob school_office_spread_prob immunize_prob \
                testing_prob quarantine_prob split_classes family.nbrs school.nbrs office.nbrs out.csv')
        quit()

    sim_iters = int(sys.argv[1])
    family_spread_prob = float(sys.argv[2])
    school_office_spread_prob = float(sys.argv[3])
    immunize_prob = float(sys.argv[4])
    testing_prob = float(sys.argv[5])
    quarantine_prob = float(sys.argv[6])
    split_classes = sys.argv[7] == 'true'
    family_nbrs_path = sys.argv[8]
    school_nbrs_path = sys.argv[9]
    office_nbrs_path = sys.argv[10]
    out_path = sys.argv[11]

    epsim = Epsim()
    epsim.init_from_files(family_nbrs_path, school_nbrs_path, office_nbrs_path, split_classes)
    x_rounds, y_num_infected = epsim.run_sim(sim_iters, family_spread_prob, school_office_spread_prob, \
                                immunize_prob, testing_prob, quarantine_prob)

    with open(out_path, 'w') as f:
        for i in range(len(x_rounds)):
            f.write('{}, {}\n'.format(x_rounds[i], y_num_infected[i]))
