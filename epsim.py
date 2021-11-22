import sys
import random
import math
from pathlib import Path

### node states ###
# 0 not infected
# 1 infected: incubation
# 2 infected: incubation
# 3 infected_ incubation
# 4 infected: spreading
# 5 infected: spreading
# 6 immune
num_node_states = 7


def chunks(lst, n):
    """Yield successive n-sized chunks from lst"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


class Epsim:
    def __init__(self):
        self.node_states = {}
        self.family_nbrs = {}
        self.school_nbrs_standard = {}
        self.school_nbrs_split = [{}, {}]
        self.office_nbrs = {}


    def init_from_dicts(self, family_nbrs, school_nbrs_standard, school_nbrs_split, office_nbrs):
        self.family_nbrs = family_nbrs
        self.school_nbrs_standard = school_nbrs_standard
        self.school_nbrs_split = school_nbrs_split
        self.office_nbrs = office_nbrs
        self.node_states = {node: 0 for (node, nbrs) in family_nbrs.items()}


    def init_from_files(self, family_nbrs_path, school_standard_path, school_split_0_path, school_split_1_path, office_nbrs_path):
        print('read nbrs files')
        self.read_nbrs_file(self.family_nbrs, family_nbrs_path)
        self.read_nbrs_file(self.office_nbrs, office_nbrs_path)
        self.node_states = {node: 0 for (node, nbrs) in self.family_nbrs.items()}

        if school_standard_path:
            self.read_nbrs_file(self.school_nbrs_standard, school_standard_path)
        if school_split_0_path:
            self.school_nbrs_split = []
            for p in (school_split_0_path, school_split_1_path):
                cur = {}
                self.read_nbrs_file(cur, p)
                self.school_nbrs_split.append(cur)


    def read_nbrs_file(self, nbrs_dict, nbrs_file_path):
        with open(nbrs_file_path) as f:
            for line in f:
                node, nbrs = line.split(':')
                node = int(node)
                nbrs = set(map(int, nbrs.split()))
                nbrs_dict[node] = nbrs


    def write_csv(self, file_path, states_per_rnd, info_per_rnd):
        with open(file_path, 'w') as f:
            f.write("round")
            for i in range(len(states_per_rnd[0])):
                f.write(f",state_{i}")
            for key in info_per_rnd[0].keys():
                f.write(f",{key}")
            f.write("\n")

            for rnd, states in enumerate(states_per_rnd):
                info = info_per_rnd[rnd]
                f.write(f"{rnd}")
                for state in states:
                    f.write(f",{state}")
                for val in info.values():
                    f.write(f",{val}")
                f.write("\n")


    def spread(self, nbrs_dict, spreading_nodes, prob):
        infec_nodes = set()
        for spreading_node in spreading_nodes:
            if spreading_node in nbrs_dict:
                for nbr in nbrs_dict[spreading_node]:
                    if self.node_states[nbr] == 0:
                        if random.random() < prob:
                            self.node_states[nbr] = 1
                            infec_nodes.add(nbr)
        return infec_nodes


    def test_nodes(self, nodes, prob):
        return {node for node in nodes if random.random() < prob}


    def detect_nodes(self, nodes, prob):
        return {node for node in nodes if random.random() < prob}


    def quarantine_node(self, node):
        self.quarantined[node] = 0
        self.spreading_parent_nodes.discard(node)
        self.spreading_child_nodes.discard(node)
        self.spreading_child_nodes_standard.discard(node)


    def quarantine_nodes_with_family(self, nodes):
        quarantined_nodes = set()
        for node in nodes:
            self.quarantine_node(node)
            quarantined_nodes.add(node)
            for nbr in self.family_nbrs[node]:
                self.quarantine_node(nbr)
                quarantined_nodes.add(nbr)
        return quarantined_nodes

    
    def determine_clusters(self, nbrs_dict):
        clusters = []
        nodes_to_skip = set()
        for node, nbrs in nbrs_dict.items():
            if node not in nodes_to_skip:
                clusters.append([node] + sorted(list(nbrs)))
                nodes_to_skip.update(nbrs)
        return clusters


    def run_sim(self, sim_iters, num_start_nodes, perc_immunized_nodes, start_weekday, p_spread_family, p_spread_school, p_spread_office, p_detect_child, 
                p_detect_parent, p_testing, print_progress=False, export_csv=False):
        """
        Run the epidemic simulation with the given parameters.

        sim_iters -- number of iterations/rounds to simulate
        num_start_nodes -- number of initially infecteded nodes
                           can be a single value, where the nodes get disributed equally over all states, or a list with the exact number of nodes per state
        perc_immunized_nodes -- percentage of initially immunized nodes
                                can be a single value, where the nodes are randomly chosen, or a dict with the percentage of nodes per node class
                                (families, parents, children)
        start_weekday -- weekday to start the simulation with (0: Monday, 1: Tuesday, ..., 6: Sunday)
        p_spread_family -- probability to spread the infection within the family
        p_spread_school -- probability to spread the infection within the school
        p_spread_office -- probability to spread the infection within the office
        p_detect_child -- probability that an infected child gets detected and quarantined because of its symtoms
        p_detect_parent -- probability that an infected parent gets detected and quarantined because of its symtoms
        p_testing -- probability that a test detects an infected person
                     dict of weekday (0 to 6) and test probability
        print_progress -- print simulation statistics every round onto the console
        export_csv -- export simulation statistics to a csv file
        """
        print("initializing simulation")

        for node in self.node_states:
            self.node_states[node] = 0

        # print graph statistics
        children = list(self.school_nbrs_standard.keys()) + list(self.school_nbrs_split[0].keys()) + list(self.school_nbrs_split[1].keys())
        print(f"children: {len(children)}")
        parents = self.office_nbrs.keys()
        print(f"parents: {len(parents)}")
        families = self.determine_clusters(self.family_nbrs)
        print(f"families: {len(families)}")

        # input conversion
        if isinstance(perc_immunized_nodes, tuple):
            perc_immunized_nodes = dict(perc_immunized_nodes)
        if isinstance(p_testing, tuple):
            p_testing = dict(p_testing)

        # immunize nodes
        if isinstance(perc_immunized_nodes, float):
            for node in random.sample(self.node_states.keys(), int(perc_immunized_nodes * len(self.node_states))):
                self.node_states[node] = 6
        elif isinstance(perc_immunized_nodes, dict):
            if 'families' in perc_immunized_nodes:
                for cluster in random.sample(families, int(perc_immunized_nodes['families'] * len(families))):
                    for node in cluster:
                        self.node_states[node] = 6
            if 'parents' in perc_immunized_nodes:
                for node in random.sample(parents, int(perc_immunized_nodes['parents'] * len(parents))):
                    self.node_states[node] = 6
            if 'children' in perc_immunized_nodes:
                for node in random.sample(children, int(perc_immunized_nodes['children'] * len(children))):
                    self.node_states[node] = 6
        else:
            raise ValueError("perc_immunized_nodes has wrong format")

        num_start_immunized = len([node for node, state in self.node_states.items() if state == 6])
        
        # set starting nodes
        if isinstance(num_start_nodes, int):
            num_start_nodes = [int(num_start_nodes / 5)] * 5
        if not isinstance(num_start_nodes, list) and len(num_start_nodes) != num_node_states - 2:  # without not infected and immune states
            raise ValueError("num_start_nodes has wrong format")
        sampled_nodes = random.sample([node for node, state in self.node_states.items() if state == 0], sum(num_start_nodes))  # ensure starting and immunized nodes don't overlap
        start_nodes_per_state = [[sampled_nodes.pop() for i in range(num)] for num in num_start_nodes]
        for i, start_nodes in enumerate(start_nodes_per_state, 1):
            for node in start_nodes:
                self.node_states[node] = i

        # print simulation info
        print(f"starting simulation with n={len(self.node_states)}, num_start_nodes={num_start_nodes}, perc_immunized_nodes={perc_immunized_nodes}, " \
              + f"start_weekday={start_weekday}, sim_iters={sim_iters}")
        print(f"p_spread_family={p_spread_family}, p_spread_school={p_spread_school}, p_spread_office={p_spread_office}, p_detect_child={p_detect_child}, " \
              + f"p_detect_parent={p_detect_parent}, p_testing={p_testing}")
        print(f"family_nbrs: {len(self.family_nbrs)}, school_nbrs_standard: {len(self.school_nbrs_standard)}, " \
              + f"school_nbrs_split: {len(self.school_nbrs_split[0])} {len(self.school_nbrs_split[1])}, office_nbrs: {len(self.office_nbrs)}")
        print(f"num_start_immunized={num_start_immunized}")

        if print_progress:
            print("the following information represents the number of nodes per round for:")
            print("round:  [state_0, state_1, state_2, state_3, state_4, state_5, state_6]" \
                  + "  [infec_family, infec_school, infec_office, infec_children, infec_parents, quarantined_detect, quarantined_test]")

        num_infec_per_rnd = []
        states_per_rnd = []
        info_per_rnd = []
        self.quarantined = {}

        # run simulation
        for rnd in range(sim_iters):
            weekday = (rnd + start_weekday) % 7

            # compute spreading nodes for this round
            self.infec_nodes = {node for node, state in self.node_states.items() if state in [1, 2, 3, 4, 5]}

            self.spreading_parent_nodes = {node for node, state in self.node_states.items() if \
                                           state in [4, 5] \
                                           and node in self.office_nbrs}
            self.spreading_child_nodes = {node for node, state in self.node_states.items() if \
                                          state in [4, 5] \
                                          and (
                                            node in self.school_nbrs_standard \
                                            or node in self.school_nbrs_split[0] \
                                            or node in self.school_nbrs_split[1])}
            self.spreading_child_nodes_standard = {node for node in self.spreading_child_nodes if node in self.school_nbrs_standard}

            # nodes in quarantine for 10 rounds get released
            self.quarantined = {node: counter for (node, counter) in self.quarantined.items() if counter < 10}

            # split between quarantined and non-quarantined spreading nodes
            self.quarantined_spreading_parent_nodes = {node for node in self.quarantined if node in self.spreading_parent_nodes}
            self.quarantined_spreading_child_nodes = {node for node in self.quarantined if node in self.spreading_child_nodes}
            self.spreading_parent_nodes = {node for node in self.spreading_parent_nodes if node not in self.quarantined}
            self.spreading_child_nodes = {node for node in self.spreading_child_nodes if node not in self.quarantined}
            self.spreading_child_nodes_standard = {node for node in self.spreading_child_nodes_standard if node not in self.quarantined}

            # spread the infection
            # for quarantined nodes spread only in family
            infec_family_children = self.spread(self.family_nbrs, self.quarantined_spreading_child_nodes, p_spread_family)
            infec_family_parents = self.spread(self.family_nbrs, self.quarantined_spreading_parent_nodes, p_spread_family)

            # spread in family every day
            infec_family_children = infec_family_children.union(self.spread(self.family_nbrs, self.spreading_child_nodes, p_spread_family))
            infec_family_parents = infec_family_parents.union(self.spread(self.family_nbrs, self.spreading_parent_nodes, p_spread_family))

            # children are tested on monday, wednesday and friday and if they test positive, them and their families get quarantined
            quarantined_test = set()
            if weekday in p_testing:
                pos_tested_children = self.test_nodes(self.spreading_child_nodes, p_testing[weekday])
                quarantined_test = self.quarantine_nodes_with_family(pos_tested_children)

            # spread in office and school only during weekdays
            infec_office = set()
            quarantined_detect_office = set()
            infec_school_standard = set()
            infec_school_split = set()
            quarantined_detect_standard = set()
            quarantined_detect_split = set()
            if weekday in [0, 1, 2, 3, 4]:
                # spread in office
                infec_office = self.spread(self.office_nbrs, self.spreading_parent_nodes, p_spread_office)
                # with p_detect_parent an infection of a parent gets detected (shows symtoms) and it and its family gets quarantined
                detect_office = self.detect_nodes(infec_office, p_detect_parent)
                quarantined_detect_office = self.quarantine_nodes_with_family(detect_office)

                # handle standard classes
                if len(self.school_nbrs_standard) > 0:
                    infec_school_standard = self.spread(self.school_nbrs_standard, self.spreading_child_nodes, p_spread_school)
                    # with p_detect_child an infection of a child gets detected (shows symtoms) and it and its family gets quarantined
                    detect_standard = self.detect_nodes(infec_school_standard, p_detect_child)
                    quarantined_detect_standard = self.quarantine_nodes_with_family(detect_standard)

                # handle alternating split classes
                if len(self.school_nbrs_split[0]) > 0:
                    current_class = rnd % 2
                    infec_school_split = self.spread(self.school_nbrs_split[current_class], self.spreading_child_nodes, p_spread_school)
                    detect_split = self.detect_nodes(infec_school_split, p_detect_child)
                    quarantined_detect_split = self.quarantine_nodes_with_family(detect_split)

            # all infected nodes increase their state every round
            for infec_node in self.infec_nodes:
                self.node_states[infec_node] += 1
            # increase quarantine counter for every quarantined node
            for quarantined_node in self.quarantined:
                self.quarantined[quarantined_node] += 1

            # info tracking
            states_per_rnd.append([0] * num_node_states)
            for state in self.node_states.values():
                states_per_rnd[rnd][state] += 1
            info_per_rnd.append({
                'infec_family': len(infec_family_children) + len(infec_family_parents),
                'infec_school': len(infec_school_standard) + len(infec_school_split),
                'infec_office': len(infec_office),
                'infec_children': len(infec_family_children) + len(infec_school_standard) + len(infec_school_split),
                'infec_parents': len(infec_family_parents) + len(infec_office),
                'quarantined_detect': len(quarantined_detect_office) + len(quarantined_detect_standard) + len(quarantined_detect_split),
                'quarantined_test': len(quarantined_test)})
            if print_progress:
                print(f"{rnd}:\t{states_per_rnd[rnd]}\t{list(info_per_rnd[rnd].values())}")

            num_infec = sum(states_per_rnd[rnd][1:])
            num_infec_per_rnd.append(num_infec)

        print(f"total infected nodes: {num_infec - num_start_immunized}\n")
        if export_csv:
            self.write_csv(export_csv, states_per_rnd, info_per_rnd)
        return num_infec_per_rnd
