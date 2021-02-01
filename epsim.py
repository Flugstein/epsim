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
        self.cluster_nbrs = {}
        self.grid_nbrs = {}
        self.b_cluster_nbrs = {}
    

    def init_clusters(self, cluster_nbrs, grid_nbrs, b_cluster_nbrs):
        self.node_states = {node: 0 for (node, nbrs) in cluster_nbrs.items()}
        self.cluster_nbrs = cluster_nbrs
        self.grid_nbrs = grid_nbrs
        self.b_cluster_nbrs = b_cluster_nbrs


    def read_cluster_files(self, cluster_nbrs_path, grid_nbrs_path, b_cluster_nbrs_path):
        print('read cluster files')
        self.node_states = {}
        
        self.cluster_nbrs = {}
        with open(cluster_nbrs_path) as f:
            for line in f:
                node, nbrs = line.split(':')
                node = int(node)
                nbrs = set(map(int, nbrs.split()))
                self.cluster_nbrs[node] = nbrs
                self.node_states[node] = 0

        self.grid_nbrs = {}
        with open(grid_nbrs_path) as f:
            for line in f:
                node, nbrs = line.split(':')
                node = int(node)
                nbrs = set(map(int, nbrs.split()))
                self.grid_nbrs[node] = nbrs

        self.b_cluster_nbrs = {}
        with open(b_cluster_nbrs_path) as f:
            for line in f:
                node, nbrs = line.split(':')
                node = int(node)
                nbrs = set(map(int, nbrs.split()))
                self.b_cluster_nbrs[node] = nbrs


    def spread_1(self, spreading_nodes, prob):
        for spreading_node in spreading_nodes:
            for nbr in self.cluster_nbrs[spreading_node]:
                if self.node_states[nbr] == 0:
                    if random.random() < prob:
                        self.node_states[nbr] = 1


    def spread_2(self, spreading_nodes, prob):
        inf_a_nodes = []
        for spreading_node in spreading_nodes:
            if spreading_node in self.grid_nbrs:
                for nbr in self.grid_nbrs[spreading_node]:
                    if self.node_states[nbr] == 0:
                        if random.random() < prob:
                            self.node_states[nbr] = 1
                            inf_a_nodes.append(nbr)
            if spreading_node in self.b_cluster_nbrs:
                for nbr in self.b_cluster_nbrs[spreading_node]:
                    if self.node_states[nbr] == 0:
                        if random.random() < prob:
                            self.node_states[nbr] = 1
        return inf_a_nodes


    def immunize_a_cluster_nbrs(self, inf_a_nodes, prob):
        for inf_a_node in inf_a_nodes:
            if random.random() < prob:
                for nbr in self.cluster_nbrs[inf_a_node]:
                    self.node_states[nbr] = 5

                    
    def run_sim(self, sim_iters, stage1_prob, stage2_prob, immunize_prob):
        num_start = int(2*math.log(len(self.node_states)))
        start_nodes = random.sample(self.node_states.keys(), num_start)
        for v in self.node_states:
            self.node_states[v] = 0
        for v in start_nodes:
            self.node_states[v] = 1

        print('starting simulation with n={}, num_start_nodes={}, sim_iters={}, stage1_prob={}, stage2_prob={}, immunize_prob={}'.format(len(self.node_states), len(start_nodes), sim_iters, stage1_prob, stage2_prob, immunize_prob))
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

            self.spread_1(spreading_nodes, stage1_prob)
            inf_a_nodes = self.spread_2(spreading_nodes, stage2_prob)
            self.immunize_a_cluster_nbrs(inf_a_nodes, immunize_prob)

            for inf_node in inf_nodes:
                self.node_states[inf_node] += 1

            num_inf = sum([1 for v in self.node_states.keys() if self.node_states[v] > 0])
            x_rounds.append(rnd)
            y_num_infected.append(num_inf)

        print('infected nodes: {}'.format(num_inf))
        print()
        return x_rounds, y_num_infected


if __name__ == '__main__':
    if len(sys.argv) != 7:
        print('usage: python sim.py sim_iters stage1_prob stage2_prob immunize_prob cluster_nbrs.clust grid_nbrs.clust b_cluster_nbrs.clust out.csv')
        quit()

    sim_iters = int(sys.argv[1])
    stage1_prob = float(sys.argv[2])
    stage2_prob = float(sys.argv[3])
    immunize_prob = float(sys.argv[4])
    cluster_nbrs_path = sys.argv[5]
    grid_nbrs_path = sys.argv[6]
    b_cluster_nbrs_path = sys.argv[7]
    out_path = sys.argv[8]

    epsim = Epsim()
    epsim.read_cluster_files(cluster_nbrs_path, grid_nbrs_path, b_cluster_nbrs_path)
    x_rounds, y_num_infected = epsim.run_sim(sim_iters, stage1_prob, stage2_prob, immunize_prob)

    with open(out_path, 'w') as f:
        for i in range(len(x_rounds)):
            f.write('{}, {}\n'.format(x_rounds[i], y_num_infected[i]))
