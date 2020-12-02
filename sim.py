import sys
import numpy as np
import random
import math

if len(sys.argv) != 3:
    print('usage: python sim.py cluster_nbrs.clust grid_nbrs.clust')
    quit()

cluster_nbrs_path = sys.argv[1]
grid_nbrs_path = sys.argv[2]


# read cluster files
print('read cluster files')
node_states = {}
cluster_nbrs = {}
with open(cluster_nbrs_path) as f:
    for line in f:
        node, nbrs = line.split(':')
        node = int(node)
        nbrs = set(map(int, nbrs.split()))
        cluster_nbrs[node] = nbrs
        node_states[node] = 0

grid_nbrs = {}
with open(grid_nbrs_path) as f:
    for line in f:
        node, nbrs = line.split(':')
        node = int(node)
        nbrs = set(map(int, nbrs.split()))
        grid_nbrs[node] = nbrs


# sim stages
def spread_1(inf_nodes):
    for inf_node in inf_nodes:
        for nbr in cluster_nbrs[inf_node]:
            if node_states[nbr] == 0:
                if random.random() < 0.3:
                    node_states[nbr] = 1


def spread_2(inf_nodes):
    for inf_node in inf_nodes:
        if inf_node in grid_nbrs:
            for nbr in grid_nbrs[inf_node]:
                if node_states[nbr] == 0:
                    if random.random() < 0.2:
                        node_states[nbr] = 1


# run sim
print('run sim')
num_start = int(2*math.log(len(node_states)))
start_nodes = random.sample(node_states.keys(), num_start)
for v in start_nodes:
    node_states[v] = 1

sim_iter = int(2*math.log(len(node_states)))

print('n: {}'.format(len(node_states)))
print('start nodes: {}'.format(len(start_nodes)))
print('iterations: {}'.format(sim_iter))

for i in range(sim_iter):
    inf_nodes = [v for v in node_states.keys() if node_states[v] >= 1 and node_states[v] <= 2]
    spread_1(inf_nodes)
    spread_2(inf_nodes)
    for inf_node in inf_nodes:
        node_states[inf_node] += 1
    print(i, end='\r')

num_inf = sum([1 for v in node_states.keys() if node_states[v] > 0])

print('infected nodes: {}'.format(num_inf))
