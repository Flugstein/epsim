import sys
import random
import math
import numpy as np
from pathlib import Path


def chunks(lst, n):
    """Yield successive n-sized chunks from lst"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


class EpsimGraph:
    def __init__(self, k, sigma_office, perc_split_classes, print_progress=False):
        """
        Generate a graph for epidemic simulation with the given parameters.
        
        k -- determines the number of nodes in the graph (will be approx. 2*k)
        sigma_office -- determines the distribution of parents to the offices
        perc_split_classes -- percentage of school classes that are split in half and alternate a shared classroom every day
        """
        self.k = k
        self.perc_split_classes = perc_split_classes
        self.nodes = {i: True for i in range(2*k)}
        self.sigma_office = sigma_office
        self.id_bump = 2*k
        self.child_nodes = set(range(k))
        self.parent_nodes = set(range(k, 2*k))
        self.family_nbrs = {}
        self.school_nbrs_standard = {}
        self.school_nbrs_split = [] # list of 2 dicts
        self.office_nbrs = {}
        self.print_progress = print_progress

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
                f.write(f"{node}: ")
                if len(nbrs) == 0:
                    f.write("\n")
                else:
                    for nbr in nbrs[:-1]:
                        f.write(f"{nbr} ")
                    f.write(f"{nbrs[-1]}\n")


    def write(self, family_nbrs_path, school_nbrs_path, office_nbrs_path):
        # continous node ids starting from 0
        old2new = {}
        for i, node in enumerate(list(self.nodes.keys())):
            old2new[node] = i

        new_family_nbrs = self.conv2new(self.family_nbrs, old2new)
        self.write_nbrs(new_family_nbrs, family_nbrs_path)
        print(f"{family_nbrs_path} written")

        if len(self.school_nbrs_standard) > 0:
            nbrs = self.conv2new(self.school_nbrs_standard, old2new)
            path = school_nbrs_path.with_stem(school_nbrs_path.stem + "_standard")
            self.write_nbrs(nbrs, path)
            print(f'{path} written')

        if len(self.school_nbrs_split[0]) > 0:
            for i in range(len(self.school_nbrs_split)):
                nbrs = self.conv2new(self.school_nbrs_split[i], old2new)
                path = school_nbrs_path.with_stem(school_nbrs_path.stem + f"_split_{i}")
                self.write_nbrs(nbrs, path)
                print(f'{path} written')

        new_office_nbrs = self.conv2new(self.office_nbrs, old2new)
        self.write_nbrs(new_office_nbrs, office_nbrs_path)
        print(f"{office_nbrs_path} written")


    def create_graph(self):
        print(f"creating graph with k={self.k}, sigma_office={self.sigma_office}")
        if self.print_progress:
            print("randomly cluster children and parent nodes, such that there are child-parent pairs")
        children2parents = list(self.parent_nodes)
        random.shuffle(children2parents)
        for child_node, parent_node in enumerate(children2parents):
            self.family_nbrs[child_node] = {parent_node}
            self.family_nbrs[parent_node] = {child_node}

        # parents: 1/2 no change, 1/4 merge 2 nodes, 1/8 merge 3 nodes, ...
        if self.print_progress:
            print("parents: 1/2 no change, 1/4 merge 2, 1/8 merge 3, ...")
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

        # parents: duplicate every node
        if self.print_progress:
            print("parents: duplicate")
        parent_nodes = self.parent_nodes.copy()
        for parent_node in parent_nodes:
            self.duplicate_parents(parent_node)

        # children: k/l^2 many l*l grids, randomly place l^2 nodes on grid, cluster 8-neighbourhood
        # perc_split_classes of grids (school classes) are divided into 2, with a sparser grid
        l = 5
        if self.print_progress:
            print(f"children: {self.k}/{l}^2 many {l}*{l} grids, randomly place {l}^2 nodes on grid, cluster 8-nbrhood")
            print(f"{self.perc_split_classes*100:.0f}% of grids (school classes) are divided into 2, with a sparser grid")
        children_shuffle = list(self.child_nodes)
        random.shuffle(children_shuffle)
        children_splits = list(chunks(children_shuffle, l*l))
        if len(children_splits[-1]) != l*l:  # skip remainder
            children_splits = children_splits[:-1]

        def make_grid(skip, splits):
            adjlist = {}

            for children_split in splits:
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

        brkpnt = int(len(children_splits) * self.perc_split_classes)
        self.school_nbrs_split = [make_grid(x, children_splits[:brkpnt]) for x in {0,1}]
        self.school_nbrs_standard = make_grid(2, children_splits[brkpnt:])
        if self.print_progress:
            print(f"{len(self.school_nbrs_split[0]) + len(self.school_nbrs_split[1])} children in split classes, " \
                + f"{len(self.school_nbrs_standard)} children in standard classes ({len(children_shuffle)} total, break: {brkpnt})")

        # parents: cluster 1-sigma_office no change, sigma_office*1/2 cluster 2 nodes, sigma_office*1/4 cluster 3 nodes, 
        # sigma_office*1/8 cluster 4 nodes, sigma_office*1/8 cluster 5 nodes
        if self.print_progress:
            print(f"parents: cluster 1-{self.sigma_office} no change, {self.sigma_office}*1/2 cluster 2, {self.sigma_office}*1/4 cluster 3, ...")
        parents_shuffle = list(self.parent_nodes)
        random.shuffle(parents_shuffle)
        parents_splits = []
        divisor = 2
        cap = 16
        len_sum = 0
        parents_split = parents_shuffle[len_sum : len_sum + int(math.ceil(len(self.parent_nodes) * (1 - self.sigma_office)))]
        parents_splits.append(parents_split)
        len_sum += len(parents_split)
        while len_sum < len(self.parent_nodes):
            parents_split = parents_shuffle[len_sum : len_sum + int(math.ceil(len(self.parent_nodes) * self.sigma_office / divisor))]
            parents_splits.append(parents_split)
            len_sum += len(parents_split)
            divisor *= 2
            if divisor > cap:
                parents_split = parents_shuffle[len_sum:]
                parents_splits.append(parents_split)
                break

        for node in parents_splits[0]: # 1-sigma_office split
            self.office_nbrs[node] = {}

        cluster_size = 2
        for parents_split in parents_splits[1:]:  # skip 1-sigma_office split
            cluster_splits = list(chunks(parents_split, cluster_size))
            for cluster_split in cluster_splits:
                for node in cluster_split:
                    nbrs = set(cluster_split)
                    nbrs.remove(node)
                    self.office_nbrs[node] = nbrs
            cluster_size += 1

        print()
