import sys
import numpy as np
import random
import math

def chunks(lst, n):
    '''Yield successive n-sized chunks from lst'''
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


class Graph:
    def __init__(self, k):
        self.nodes = {i: set() for i in range(2*k)}
        self.id_bump = 2*k
        self.a = set(range(k))
        self.b = set(range(k, 2*k))
        self.clusters = []

    def add_edge(self, v, u):
        self.nodes[v].add(u)
        self.nodes[u].add(v)

    def rem_edge(self, v, u):
        self.nodes[v].remove(u)
        self.nodes[u].remove(v)

    def merge(self, kept_node, merge_nodes):
        for merge_node in merge_nodes:
            merge_node_nbrs = self.nodes[merge_node].copy()
            for merge_node_nbr in merge_node_nbrs:
                self.add_edge(kept_node, merge_node_nbr)
                self.rem_edge(merge_node_nbr, merge_node)
            self.nodes.pop(merge_node)
            self.a.discard(merge_node)
            self.b.discard(merge_node)

    def duplicate(self, node):
        new_node = self.id_bump
        self.nodes[new_node] = set()
        for nbr in self.nodes[node]:
            self.add_edge(new_node, nbr)

        if node in self.a:
            self.a.add(new_node)
        elif node in self.b:
            self.b.add(new_node)
        
        self.id_bump += 1

    def add_cluster(self, nodes):
        self.clusters.append(set(nodes))

    def write(self, graph_path, cluster_path):
        # continous node ids starting from 1
        old2new = {}
        i = 1
        for node in sorted(list(self.nodes.keys()), key=lambda _id: len(self.nodes[_id]), reverse=True):
            old2new[node] = i
            i += 1

        # write graph file
        num_edges = 0
        new_nodes = [[] for i in range(len(self.nodes))]
        for old_id, old_adj in self.nodes.items():
            new_adj = sorted([old2new[old_nbr] for old_nbr in old_adj])
            new_nodes[old2new[old_id] - 1] = new_adj
            num_edges += len(new_adj)
        
        with open(graph_path, 'w') as f:
            f.write('{} {}\n'.format(len(new_nodes), num_edges))
            for adj in new_nodes:
                if len(adj) == 0:
                    f.write('\n')
                else:
                    for i in adj[:-1]:
                        f.write('{} '.format(i))
                    f.write('{}\n'.format(adj[-1]))
        print('graph written')
        
        # write clusters file
        new_clusters = []
        for cluster in self.clusters:
            new_cluster = sorted([old2new[old_id] for old_id in cluster])
            new_clusters.append(new_cluster)
        new_clusters = sorted(new_clusters, key=len, reverse=True)

        with open(cluster_path, 'w') as f:
            for cluster in new_clusters:
                for i in cluster[:-1]:
                    f.write('{} '.format(i))
                f.write('{}\n'.format(cluster[-1]))
        print('clusters written')


if len(sys.argv) != 4:
    print('usage: python gengraph.py k out.metis out.clust')
    quit()

k = int(sys.argv[1])
graph_path = sys.argv[2]
cluster_path = sys.argv[3]

print('create graph')
g = Graph(k)

print('randomly connect nodes between a and b, such that every node has degree 1')
a2b = list(g.b)
random.shuffle(a2b)
for a_node, b_node in enumerate(a2b):
    g.add_edge(a_node, b_node)

print('b: 1/2 no change, 1/4 merge 2 nodes, 1/8 merge 3 nodes, ...')
b_shuffle = list(g.b)
random.shuffle(b_shuffle)
b_splits = []
divisor = 2
len_sum = 0
while len_sum < len(g.b):
    b_split = b_shuffle[len_sum : len_sum + int(math.ceil(len(g.b) / divisor))]
    b_splits.append(b_split)
    len_sum += len(b_split)
    divisor *= 2

merge_size = 2
for b_split in b_splits[1:]:  # skip 1/2 split
    merge_splits = list(chunks(b_split, merge_size))
    for merge_split in merge_splits:
        g.merge(merge_split[0], merge_split[1:])
    merge_size += 1

print('b: duplicate every node')
b_nodes = g.b.copy()
for b_node in b_nodes:
    g.duplicate(b_node)

print('a: k/l^2 many l*l grids, place l^2 nodes randomly on grid, add edges between 8 neighbourhood')
l = 5
a_shuffle = list(g.a)
random.shuffle(a_shuffle)
a_splits = list(chunks(a_shuffle, l*l))
if len(a_splits[-1]) != l*l:  # skip remainder
    a_splits = a_splits[:-1]

for a_split in a_splits:
    grid = np.reshape(a_split, (l, l))

    for i, j in np.ndindex(grid.shape):
        node = grid[i][j]
        nbrs = []

        if i > 0:
            nbrs.append(grid[i-1][j])
            if j > 0:
                nbrs.append(grid[i-1][j-1])
            if j < l - 1:
                nbrs.append(grid[i-1][j+1])
            
        if j > 0:
            nbrs.append(grid[i][j-1])
        if j < l - 1:
            nbrs.append(grid[i][j+1])

        if i < l - 1:
            nbrs.append(grid[i+1][j])
            if j > 0:
                nbrs.append(grid[i+1][j-1])
            if j < l - 1:
                nbrs.append(grid[i+1][j+1])

        for nbr in nbrs:
            g.add_edge(node, nbr)

print('b: create clusters: 1/2 singe nodes, 1/4 clusters size 2, 1/8 clusters size 3, ...')
b_shuffle = list(g.b)
random.shuffle(b_shuffle)
b_splits = []
divisor = 2
len_sum = 0
while len_sum < len(g.b):
    b_split = b_shuffle[len_sum : len_sum + int(math.ceil(len(g.b) / divisor))]
    b_splits.append(b_split)
    len_sum += len(b_split)
    divisor *= 2

cluster_size = 1
for b_split in b_splits:
    cluster_splits = list(chunks(b_split, cluster_size))
    for cluster_split in cluster_splits:
        g.add_cluster(cluster_split)
    cluster_size += 1

print('write graph')
g.write(graph_path, cluster_path)
