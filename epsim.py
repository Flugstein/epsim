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
        nbrs_dict = {}
        with open(nbrs_file_path) as f:
            for line in f:
                node, nbrs = line.split(':')
                node = int(node)
                nbrs = set(map(int, nbrs.split()))
                nbrs_dict[node] = nbrs


    def spread_family(self, spreading_nodes, prob):
        for spreading_node in spreading_nodes:
            for nbr in self.family_nbrs[spreading_node]:
                if self.node_states[nbr] == 0:
                    if random.random() < prob:
                        self.node_states[nbr] = 1


    def spread_school_office(self, spreading_nodes, prob):
        infec_child_nodes = []
        for spreading_node in spreading_nodes:
            if spreading_node in self.school_nbrs:
                for nbr in self.school_nbrs[spreading_node]:
                    if self.node_states[nbr] == 0:
                        if random.random() < prob:
                            self.node_states[nbr] = 1
                            infec_child_nodes.append(nbr)
            if spreading_node in self.office_nbrs:
                for nbr in self.office_nbrs[spreading_node]:
                    if self.node_states[nbr] == 0:
                        if random.random() < prob:
                            self.node_states[nbr] = 1
        return infec_child_nodes


    def immunize_child_family_nbrs(self, infec_child_nodes, prob):
        for infec_child_node in infec_child_nodes:
            if random.random() < prob:
                for nbr in self.family_nbrs[infec_child_node]:
                    self.node_states[nbr] = 5

                    
    def run_sim(self, sim_iters, family_spread_prob, school_office_spread_prob, immunize_prob):
        num_start_nodes = int(2*math.log(len(self.node_states)))
        start_nodes = random.sample(self.node_states.keys(), num_start_nodes)
        for v in self.node_states:
            self.node_states[v] = 0
        for v in start_nodes:
            self.node_states[v] = 1

        print('starting simulation with n={}, num_start_nodes={}, sim_iters={}, family_spread_prob={}, school_office_spread_prob={}, immunize_prob={}'.format(len(self.node_states), len(start_nodes), sim_iters, family_spread_prob, school_office_spread_prob, immunize_prob))
        x_rounds = []
        y_num_infected = []

        for rnd in range(sim_iters):
            inf_nodes = []
            spreading_nodes = []
            for v in self.node_states.keys():
                if self.node_states[v] >= 1 and self.node_states[v] <= 4:
                    inf_nodes.append(v)
                    if self.node_states[v] >= 3 and self.node_states[v] <= 4:
                        spreading_nodes.append(v)

            self.spread_family(spreading_nodes, family_spread_prob)
            infec_child_nodes = self.spread_school_office(spreading_nodes, school_office_spread_prob)
            self.immunize_child_family_nbrs(infec_child_nodes, immunize_prob)

            for inf_node in inf_nodes:
                self.node_states[inf_node] += 1

            num_infeced = sum([1 for v in self.node_states.keys() if self.node_states[v] > 0])
            x_rounds.append(rnd)
            y_num_infected.append(num_infeced)

        print('infected nodes: {}'.format(num_infeced))
        print()
        return x_rounds, y_num_infected


if __name__ == '__main__':
    if len(sys.argv) != 7:
        print('usage: python epsim.py sim_iters family_spread_prob school_office_spread_prob immunize_prob family.nbrs school.nbrs office.nbrs out.csv')
        quit()

    sim_iters = int(sys.argv[1])
    family_spread_prob = float(sys.argv[2])
    school_office_spread_prob = float(sys.argv[3])
    immunize_prob = float(sys.argv[4])
    family_nbrs_path = sys.argv[5]
    school_nbrs_path = sys.argv[6]
    office_nbrs_path = sys.argv[7]
    out_path = sys.argv[8]

    epsim = Epsim()
    epsim.init_from_files(family_nbrs_path, school_nbrs_path, office_nbrs_path)
    x_rounds, y_num_infected = epsim.run_sim(sim_iters, family_spread_prob, school_office_spread_prob, immunize_prob)

    with open(out_path, 'w') as f:
        for i in range(len(x_rounds)):
            f.write('{}, {}\n'.format(x_rounds[i], y_num_infected[i]))
