import sys
import numpy as np
import random
import math

random.seed(1)

def chunks(lst, n):
    '''Yield successive n-sized chunks from lst'''
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


class Graph:
    def __init__(self, k, sigma):
        self.nodes = {i: True for i in range(2*k)}
        assert sigma > 0 and sigma <= 0.5
        self.sigma = sigma
        self.id_bump = 2*k
        self.a = set(range(k))
        self.b = set(range(k, 2*k))
        self.cluster_nbrs = {}
        self.grid_nbrs = {}
        self.b_cluster_nbrs = {}

        self.create_graph()
    

    def merge_b(self, kept_node, merge_nodes):
        for merge_node in merge_nodes:
            for node in self.cluster_nbrs[merge_node]:
                self.cluster_nbrs[node].add(kept_node)
                self.cluster_nbrs[node].update(self.cluster_nbrs[kept_node])

            for node in self.cluster_nbrs[merge_node]:
                self.cluster_nbrs[node].discard(merge_node)

            for node in self.cluster_nbrs[kept_node]:
                self.cluster_nbrs[node].update(self.cluster_nbrs[merge_node])
            self.cluster_nbrs[kept_node].update(self.cluster_nbrs[merge_node])

            self.cluster_nbrs.pop(merge_node)

            self.nodes.pop(merge_node)
            self.b.discard(merge_node)
    

    def duplicate_b(self, original):
        new_node = self.id_bump

        self.nodes[new_node] = True
        self.b.add(new_node)

        self.cluster_nbrs[new_node] = set()
        self.cluster_nbrs[new_node].update(self.cluster_nbrs[original])
        self.cluster_nbrs[new_node].add(original)

        for node in self.cluster_nbrs[original]:
            self.cluster_nbrs[node].add(new_node)
        self.cluster_nbrs[original].add(new_node)
        
        self.id_bump += 1


    def write(self, cluster_nbrs_path, grid_nbrs_path, b_cluster_nbrs_path):
        # continous node ids starting from 0
        old2new = {}
        i = 1
        for node in list(self.nodes.keys()):
            old2new[node] = i
            i += 1

        # write cluster_nbrs file
        new_cluster_nbrs = {}
        for old_id, old_cluster in self.cluster_nbrs.items():
            new_cluster = sorted([old2new[old_nbr] for old_nbr in old_cluster])
            new_cluster_nbrs[old2new[old_id]] = new_cluster
        
        with open(cluster_nbrs_path, 'w') as f:
            for _id in sorted(new_cluster_nbrs.keys()):
                cluster = new_cluster_nbrs[_id]
                f.write('{}: '.format(_id))
                if len(cluster) == 0:
                    f.write('\n')
                else:
                    for i in cluster[:-1]:
                        f.write('{} '.format(i))
                    f.write('{}\n'.format(cluster[-1]))
        print('cluster nbrs written')
        
        # write grid_nbrs file
        new_grid_nbrs = {}
        for old_id, old_grid in self.grid_nbrs.items():
            new_grid = sorted([old2new[old_nbr] for old_nbr in old_grid])
            new_grid_nbrs[old2new[old_id]] = new_grid
        
        with open(grid_nbrs_path, 'w') as f:
            for _id in sorted(new_grid_nbrs.keys()):
                grid = new_grid_nbrs[_id]
                f.write('{}: '.format(_id))
                if len(grid) == 0:
                    f.write('\n')
                else:
                    for i in grid[:-1]:
                        f.write('{} '.format(i))
                    f.write('{}\n'.format(grid[-1]))
        print('grid nbrs written')

        # write b_cluster_nbrs file
        new_cluster_nbrs = {}
        for old_id, old_cluster in self.b_cluster_nbrs.items():
            new_cluster = sorted([old2new[old_nbr] for old_nbr in old_cluster])
            new_cluster_nbrs[old2new[old_id]] = new_cluster
        
        with open(b_cluster_nbrs_path, 'w') as f:
            for _id in sorted(new_cluster_nbrs.keys()):
                cluster = new_cluster_nbrs[_id]
                f.write('{}: '.format(_id))
                if len(cluster) == 0:
                    f.write('\n')
                else:
                    for i in cluster[:-1]:
                        f.write('{} '.format(i))
                    f.write('{}\n'.format(cluster[-1]))
        print('b cluster nbrs written')


    def create_graph(self):
        print('randomly cluster nodes of a and b, such that there are a,b pairs')
        a2b = list(self.b)
        random.shuffle(a2b)
        for a_node, b_node in enumerate(a2b):
            self.cluster_nbrs[a_node] = {b_node}
            self.cluster_nbrs[b_node] = {a_node}

        print('b: 1/2 no change, 1/4 merge 2 nodes, 1/8 merge 3 nodes, ...')
        b_shuffle = list(self.b)
        random.shuffle(b_shuffle)
        b_splits = []
        divisor = 2
        len_sum = 0
        while len_sum < len(self.b):
            b_split = b_shuffle[len_sum : len_sum + int(math.ceil(len(self.b) / divisor))]
            b_splits.append(b_split)
            len_sum += len(b_split)
            divisor *= 2

        merge_size = 2
        for b_split in b_splits[1:]:  # skip 1/2 split
            merge_splits = list(chunks(b_split, merge_size))
            for merge_split in merge_splits:
                self.merge_b(merge_split[0], merge_split[1:])
            merge_size += 1

        print('b: duplicate every node')
        b_nodes = self.b.copy()
        for b_node in b_nodes:
            self.duplicate_b(b_node)

        l = 5
        print('a: k/l^2 many l*l grids, place l^2 nodes randomly on grid, cluster 8 neighbourhood, with l={}'.format(l))
        a_shuffle = list(self.a)
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

                self.grid_nbrs[node] = set(nbrs)

        print('b: cluster 1-sigma no change, sigma*1/2 cluster 2 nodes, sigma*1/4 cluster 3 nodes, sigma*1/8 cluster 4 nodes, sigma*1/8 cluster 5 nodes')
        b_shuffle = list(self.b)
        random.shuffle(b_shuffle)
        b_splits = []
        divisor = 2
        cap = 16
        len_sum = 0
        b_split = b_shuffle[len_sum : len_sum + int(math.ceil(len(self.b) * (1 - self.sigma)))]
        b_splits.append(b_split)
        len_sum += len(b_split)
        while len_sum < len(self.b):
            b_split = b_shuffle[len_sum : len_sum + int(math.ceil(len(self.b) * sigma / divisor))]
            b_splits.append(b_split)
            len_sum += len(b_split)
            divisor *= 2
            if divisor > cap:
                b_split = b_shuffle[len_sum:]
                b_splits.append(b_split)
                break

        cluster_size = 2
        for b_split in b_splits[1:]:  # skip 1-sigma split
            cluster_splits = list(chunks(b_split, cluster_size))
            for cluster_split in cluster_splits:
                for _id in cluster_split:
                    nbrs = set(cluster_split)
                    nbrs.remove(_id)
                    self.b_cluster_nbrs[_id] = nbrs
            cluster_size += 1

if len(sys.argv) != 6:
    print('usage: python gencluster.py k sigma cluster_nbrs.clust grid_nbrs.clust b_cluster_nbrs.clust')
    quit()

k = int(sys.argv[1])
sigma = float(sys.argv[2])
cluster_nbrs_path = sys.argv[3]
grid_nbrs_path = sys.argv[4]
b_cluster_nbrs_path = sys.argv[5]

print('create graph')
g = Graph(k, sigma)
print('nodes: {}'.format(len(g.nodes)))
g.write(cluster_nbrs_path, grid_nbrs_path, b_cluster_nbrs_path)
