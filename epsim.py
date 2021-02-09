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

class Epsim:
    def __init__(self):
        self.node_states = {}
        self.family_nbrs = {}
        self.school_nbrs = {}
        self.office_nbrs = {}


    def init_from_dicts(self, family_nbrs, school_nbrs, office_nbrs):
        self.family_nbrs = family_nbrs
        self.school_nbrs = school_nbrs
        self.office_nbrs = office_nbrs
        self.node_states = {node: 0 for (node, nbrs) in family_nbrs.items()}


    def init_from_files(self, family_nbrs_path, school_nbrs_path, office_nbrs_path):
        print('read nbrs files')
        self.read_nbrs_file(self.family_nbrs, family_nbrs_path)
        self.read_nbrs_file(self.school_nbrs, school_nbrs_path)
        self.read_nbrs_file(self.office_nbrs, office_nbrs_path)
        self.node_states = {node: 0 for (node, nbrs) in self.family_nbrs.items()}


    def read_nbrs_file(self, nbrs_dict, nbrs_file_path):
        with open(nbrs_file_path) as f:
            for line in f:
                node, nbrs = line.split(':')
                node = int(node)
                nbrs = set(map(int, nbrs.split()))
                nbrs_dict[node] = nbrs


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
                    self.node_states[nbr] = 5

    def immunize_children_after_testing(self, spreading_nodes, prob):
        for spreading_node in spreading_nodes:
            if spreading_node in self.school_nbrs:
                if random.random() < prob:
                    self.node_states[spreading_node] = 5

    #similar to immunize_child_family_nbrs
    def quarantine_family(self, prob):
        immune_nodes = [node for node, state in self.node_states.items() if state >= 5]
        for node in immune_nodes:
            if random.random() < prob:
                for nbr in self.family_nbrs[node]:
                    self.node_states[nbr] = 5



    def run_sim(self, sim_iters, family_spread_prob, school_office_spread_prob, immunize_prob, testing_prob, quarantine_prob):
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

        for rnd in range(sim_iters):
            weekday = rnd % 7

            inf_nodes = [node for node, state in self.node_states.items() if state in [1, 2, 3, 4]]
            spreading_nodes = [node for node, state in self.node_states.items() if state in [3, 4]]

            self.spread(self.family_nbrs, spreading_nodes, family_spread_prob)

            #assume children are tested on Monday morning
            if weekday == 0:
                self.immunize_children_after_testing(spreading_nodes, testing_prob)

            if weekday in [0, 1, 2, 3, 4]:
                self.spread(self.office_nbrs, spreading_nodes, school_office_spread_prob)
                infec_child_nodes = self.spread_ret(self.school_nbrs, spreading_nodes, school_office_spread_prob)
                self.immunize_child_family_nbrs(infec_child_nodes, immunize_prob)

            self.quarantine_family(quarantine_prob)

            num_infeced = sum([1 for node, state in self.node_states.items() if state > 0])
            x_rounds.append(rnd)
            y_num_infected.append(num_infeced)

            for inf_node in inf_nodes:
                self.node_states[inf_node] += 1

        print('infected nodes: {}\n'.format(num_infeced))
        return x_rounds, y_num_infected


if __name__ == '__main__':
    if len(sys.argv) != 11:
        print('usage: python epsim.py sim_iters family_spread_prob school_office_spread_prob immunize_prob \
                testing_prob quarantine_prob family.nbrs school.nbrs office.nbrs out.csv')
        quit()

    sim_iters = int(sys.argv[1])
    family_spread_prob = float(sys.argv[2])
    school_office_spread_prob = float(sys.argv[3])
    immunize_prob = float(sys.argv[4])
    testing_prob = float(sys.argv[5])
    quarantine_prob = float(sys.argv[6])
    family_nbrs_path = sys.argv[7]
    school_nbrs_path = sys.argv[8]
    office_nbrs_path = sys.argv[9]
    out_path = sys.argv[10]

    epsim = Epsim()
    epsim.init_from_files(family_nbrs_path, school_nbrs_path, office_nbrs_path)
    x_rounds, y_num_infected = epsim.run_sim(sim_iters, family_spread_prob, school_office_spread_prob, \
                                immunize_prob, testing_prob, quarantine_prob)

    with open(out_path, 'w') as f:
        for i in range(len(x_rounds)):
            f.write('{}, {}\n'.format(x_rounds[i], y_num_infected[i]))
