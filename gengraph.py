import sys
import numpy as np
import random
import math


def chunks(lst, n):
    '''Yield successive n-sized chunks from lst'''
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


class EpsimGraph:
    def __init__(self, k, office_sigma, split_classes):
        self.k = k
        self.split_classes = split_classes
        self.nodes = {i: True for i in range(2*k)}
        assert office_sigma > 0 and office_sigma <= 0.5
        self.office_sigma = office_sigma
        self.id_bump = 2*k
        self.child_nodes = set(range(k))
        self.parent_nodes = set(range(k, 2*k))
        self.family_nbrs = {}
        self.school_nbrs = [] # list of dicts
        self.office_nbrs = {}

        self.create_graph()
    

    def merge_parents(self, kept_node, merge_nodes):
        for merge_node in merge_nodes:
            for node in self.family_nbrs[merge_node]:
                self.family_nbrs[node].add(kept_node)
                self.family_nbrs[node].update(self.family_nbrs[kept_node])

            for node in self.family_nbrs[merge_node]:
                self.family_nbrs[node].discard(merge_node)

            for node in self.family_nbrs[kept_node]:
                self.family_nbrs[node].update(self.family_nbrs[merge_node])
            self.family_nbrs[kept_node].update(self.family_nbrs[merge_node])

            self.family_nbrs.pop(merge_node)

            self.nodes.pop(merge_node)
            self.parent_nodes.discard(merge_node)
    

    def duplicate_parents(self, original_node):
        new_node = self.id_bump
        self.id_bump += 1

        self.nodes[new_node] = True
        self.parent_nodes.add(new_node)

        self.family_nbrs[new_node] = set()
        self.family_nbrs[new_node].update(self.family_nbrs[original_node])
        self.family_nbrs[new_node].add(original_node)

        for node in self.family_nbrs[original_node]:
            self.family_nbrs[node].add(new_node)
        self.family_nbrs[original_node].add(new_node)
    

    def conv2new(self, nbrs_dict, old2new):
        new_nbrs_dict = {}
        for old_node, old_nbrs in nbrs_dict.items():
            new_nbrs = sorted([old2new[old_nbr] for old_nbr in old_nbrs])
            new_nbrs_dict[old2new[old_node]] = new_nbrs

        return new_nbrs_dict


    def write_nbrs(self, nbrs_dict, nbrs_file_path):
        with open(nbrs_file_path, 'w') as f:
            for node in sorted(nbrs_dict.keys()):
                nbrs = nbrs_dict[node]
                f.write('{}: '.format(node))
                if len(nbrs) == 0:
                    f.write('\n')
                else:
                    for nbr in nbrs[:-1]:
                        f.write('{} '.format(nbr))
                    f.write('{}\n'.format(nbrs[-1]))


    def write(self, family_nbrs_path, school_nbrs_path, office_nbrs_path):
        # continous node ids starting from 0
        old2new = {}
        for i, node in enumerate(list(self.nodes.keys())):
            old2new[node] = i

        new_family_nbrs = self.conv2new(self.family_nbrs, old2new)
        self.write_nbrs(new_family_nbrs, family_nbrs_path)
        print('family_nbrs written')

        for i in range(len(self.school_nbrs)):
            new_school_nbrs = self.conv2new(self.school_nbrs[i], old2new)
            self.write_nbrs(new_school_nbrs, school_nbrs_path + f'_{i}')
            print(f'school_nbrs_{i} nbrs written')

        new_office_nbrs = self.conv2new(self.office_nbrs, old2new)
        self.write_nbrs(new_office_nbrs, office_nbrs_path)
        print('office_nbrs nbrs written')


    def create_graph(self):
        print('creating graph with k={}, office_sigma={}'.format(self.k, self.office_sigma))
        print('randomly cluster children and parent nodes, such that there are child-parent pairs')
        children2parents = list(self.parent_nodes)
        random.shuffle(children2parents)
        for child_node, parent_node in enumerate(children2parents):
            self.family_nbrs[child_node] = {parent_node}
            self.family_nbrs[parent_node] = {child_node}

        print('parents: 1/2 no change, 1/4 merge 2 nodes, 1/8 merge 3 nodes, ...')
        parents_shuffle = list(self.parent_nodes)
        random.shuffle(parents_shuffle)
        parents_splits = []
        divisor = 2
        len_sum = 0
        while len_sum < len(self.parent_nodes):
            parents_split = parents_shuffle[len_sum : len_sum + int(math.ceil(len(self.parent_nodes) / divisor))]
            parents_splits.append(parents_split)
            len_sum += len(parents_split)
            divisor *= 2

        merge_size = 2
        for parents_split in parents_splits[1:]:  # skip 1/2 split
            merge_splits = list(chunks(parents_split, merge_size))
            for merge_split in merge_splits:
                self.merge_parents(merge_split[0], merge_split[1:])
            merge_size += 1

        print('parents: duplicate every node')
        parent_nodes = self.parent_nodes.copy()
        for parent_node in parent_nodes:
            self.duplicate_parents(parent_node)

        l = 5
        print('children: k/l^2 many l*l grids, place l^2 nodes randomly on grid, cluster 8 neighbourhood, with l={}'.format(l))
        children_shuffle = list(self.child_nodes)
        random.shuffle(children_shuffle)
        children_splits = list(chunks(children_shuffle, l*l))
        if len(children_splits[-1]) != l*l:  # skip remainder
            children_splits = children_splits[:-1]

        def make_grid(skip):
            adjlist = {}

            for children_split in children_splits:
                grid = np.reshape(children_split, (l, l))

                for i, j in np.ndindex(grid.shape):
                    node = grid[i][j]
                    nbrs = []

                    # skip nodes where (i+j) % 2 == skip 
                    # running with skip={1,2} gives split classes, while skip>=2 has no effect
                    if (i + j) % 2 == skip:
                        continue

                    def addUnlessSkip(i,j):
                        if (i + j) % 2 != skip:
                            nbrs.append(grid[i][j])

                    if i > 0:
                        addUnlessSkip(i-1,j)
                        if j > 0:
                            addUnlessSkip(i-1,j-1)
                        if j < l - 1:
                            addUnlessSkip(i-1,j+1)
                        
                    if j > 0:
                        addUnlessSkip(i,j-1)
                    if j < l - 1:
                        addUnlessSkip(i,j+1)

                    if i < l - 1:
                        addUnlessSkip(i+1,j)
                        if j > 0:
                            addUnlessSkip(i+1,j-1)
                        if j < l - 1:
                            addUnlessSkip(i+1,j+1)

                    adjlist[node] = set(nbrs)
            return adjlist

        self.school_nbrs = [make_grid(x) for x in ( {0,1} if split_classes else {2} )]

        print('parents: cluster 1-office_sigma no change, office_sigma*1/2 cluster 2 nodes, office_sigma*1/4 cluster 3 nodes, office_sigma*1/8 cluster 4 nodes, office_sigma*1/8 cluster 5 nodes')
        parents_shuffle = list(self.parent_nodes)
        random.shuffle(parents_shuffle)
        parents_splits = []
        divisor = 2
        cap = 16
        len_sum = 0
        parents_split = parents_shuffle[len_sum : len_sum + int(math.ceil(len(self.parent_nodes) * (1 - self.office_sigma)))]
        parents_splits.append(parents_split)
        len_sum += len(parents_split)
        while len_sum < len(self.parent_nodes):
            parents_split = parents_shuffle[len_sum : len_sum + int(math.ceil(len(self.parent_nodes) * self.office_sigma / divisor))]
            parents_splits.append(parents_split)
            len_sum += len(parents_split)
            divisor *= 2
            if divisor > cap:
                parents_split = parents_shuffle[len_sum:]
                parents_splits.append(parents_split)
                break

        cluster_size = 2
        for parents_split in parents_splits[1:]:  # skip 1-office_sigma split
            cluster_splits = list(chunks(parents_split, cluster_size))
            for cluster_split in cluster_splits:
                for node in cluster_split:
                    nbrs = set(cluster_split)
                    nbrs.remove(node)
                    self.office_nbrs[node] = nbrs
            cluster_size += 1


if __name__ == '__main__':
    if len(sys.argv) != 7:
        print('usage: python gengraph.py k office_sigma split_classes family.nbrs school.nbrs office.nbrs')
        print('\tsplit_classes: split each class into two alternating classes ("true" or "false")')
        quit()

    k = int(sys.argv[1])
    office_sigma = float(sys.argv[2])
    split_classes = sys.argv[3] == 'true'
    family_nbrs_path = sys.argv[4]
    school_nbrs_path = sys.argv[5]
    office_nbrs_path = sys.argv[6]

    print('create graph')
    g = EpsimGraph(k, office_sigma, split_classes)
    print('nodes: {}'.format(len(g.nodes)))
    g.write(family_nbrs_path, school_nbrs_path, office_nbrs_path)

