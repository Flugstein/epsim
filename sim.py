import sys
import numpy as np
import random
import math

if len(sys.argv) != 6:
    print('usage: python sim.py stage1_prop stage2_prop cluster_nbrs.clust grid_nbrs.clust b_cluster_nbrs.clust')
    quit()

stage1_prop = float(sys.argv[1])  # 0.3
stage2_prop = float(sys.argv[2])  # 0.2
cluster_nbrs_path = sys.argv[3]
grid_nbrs_path = sys.argv[4]
b_cluster_nbrs_path = sys.argv[5]


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

b_cluster_nbrs = {}
with open(b_cluster_nbrs_path) as f:
    for line in f:
        node, nbrs = line.split(':')
        node = int(node)
        nbrs = set(map(int, nbrs.split()))
        b_cluster_nbrs[node] = nbrs


# sim stages
def spread_1(spreading_nodes):
    for spreading_node in spreading_nodes:
        for nbr in cluster_nbrs[spreading_node]:
            if node_states[nbr] == 0:
                if random.random() < stage1_prop:
                    node_states[nbr] = 1


def spread_2(spreading_nodes):
    for spreading_node in spreading_nodes:
        if spreading_node in grid_nbrs:
            for nbr in grid_nbrs[spreading_node]:
                if node_states[nbr] == 0:
                    if random.random() < stage2_prop:
                        node_states[nbr] = 1
        if spreading_node in b_cluster_nbrs:
            for nbr in b_cluster_nbrs[spreading_node]:
                if node_states[nbr] == 0:
                    if random.random() < stage2_prop:
                        node_states[nbr] = 1


# run sim
print('run sim')
num_start = int(2*math.log(len(node_states)))
start_nodes = random.sample(node_states.keys(), num_start)
for v in start_nodes:
    node_states[v] = 1

sim_iter = 40

print('n: {}'.format(len(node_states)))
print('start nodes: {}'.format(len(start_nodes)))
print('iterations: {}'.format(sim_iter))

for i in range(sim_iter):
    inf_nodes = []
    spreading_nodes = []
    for v in node_states.keys():
        if node_states[v] >= 1 and node_states[v] <= 4:
            inf_nodes.append(v)
            if node_states[v] >= 3 and node_states[v] <= 4:
                spreading_nodes.append(v)

    spread_1(spreading_nodes)
    spread_2(spreading_nodes)

    for inf_node in inf_nodes:
        node_states[inf_node] += 1
    
    num_inf = sum([1 for v in node_states.keys() if node_states[v] > 0])
    print('{}: {}'.format(i, num_inf))

num_inf = sum([1 for v in node_states.keys() if node_states[v] > 0])

print('infected nodes: {}'.format(num_inf))

# 0 not infected
# 1 infected: incubation
# 2 infected: incubation
# 3 infected: spreading
# 4 infected: spreading
# 5 immune
