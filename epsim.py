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


    def immunize_node(self, node):
        self.node_states[node] = 6
        self.infec_nodes.discard(node)
        self.spreading_parent_nodes.discard(node)
        self.spreading_child_nodes.discard(node)
        self.spreading_child_nodes_standard.discard(node)


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


    def immunize_family_nbrs(self, nodes, prob):
        immunized_nodes = set()
        for node in nodes:
            if random.random() < prob:
                for nbr in self.family_nbrs[node]:
                    self.immunize_node(nbr)
                    immunized_nodes.add(nbr)
        return immunized_nodes


    def immunize_after_testing(self, spreading_nodes, prob):
        pos_tested_nodes = set()
        for spreading_node in spreading_nodes:
            if random.random() < prob:
                pos_tested_nodes.add(spreading_node)
        for node in pos_tested_nodes:
            self.immunize_node(node)
        return pos_tested_nodes


    def run_sim(self, sim_iters, num_start_nodes, num_immunized_nodes, start_weekday, p_spread_family, p_spread_school, p_spread_office, p_detect_child, 
                p_detect_parent, p_testing, print_progress=False, export_csv=False):
        """
        Run the epidemic simulation with the given parameters.

        sim_iters -- number of iterations/rounds to simulate
        num_start_nodes -- number of initially infecteded nodes
                           can be a single value, where the nodes get disributed equally over all states, or a list with the exact number of nodes per state
        num_immunized_nodes -- number of initially immunized nodes
        start_weekday -- weekday to start the simulation with (0: Monday, 1: Tuesday, ..., 6: Sunday)
        p_spread_family -- probability to spread the infection within the family
        p_spread_school -- probability to spread the infection within the school
        p_spread_office -- probability to spread the infection within the office
        p_detect_child -- probability that an infected child gets detected and quarantined because of its symtoms
        p_detect_parent -- probability that an infected parent gets detected and quarantined because of its symtoms
        p_testing -- probability that a test detects an infected person
        print_progress -- print simulation statistics every round onto the console
        export_csv -- export simulation statistics to a csv file
        """
        for node in self.node_states:
            self.node_states[node] = 0
        
        if isinstance(num_start_nodes, int):
            num_start_nodes = [int(num_start_nodes / 5)] * 5
        if not isinstance(num_start_nodes, list) and len(num_start_nodes) != num_node_states - 2:  # without not infected and immune states
            raise ValueError("num_start_nodes has wrong format")
        sampled_nodes = random.sample(self.node_states.keys(), sum(num_start_nodes))
        start_nodes_per_state = [[sampled_nodes.pop() for i in range(num)] for num in num_start_nodes]
        for i, start_nodes in enumerate(start_nodes_per_state, 1):
            for node in start_nodes:
                self.node_states[node] = i

        for node in random.sample(self.node_states.keys(), num_immunized_nodes):
            self.node_states[node] = 6

        print(f"starting simulation with n={len(self.node_states)}, num_start_nodes={num_start_nodes}, num_immunized_nodes={num_immunized_nodes}, " \
              + f"sim_iters={sim_iters}")
        print(f"p_spread_family={p_spread_family}, p_spread_school={p_spread_school}, p_spread_office={p_spread_office}, p_detect_child={p_detect_child}, " \
              + f"p_detect_parent={p_detect_parent}, p_testing={p_testing}")
        print(f"family_nbrs: {len(self.family_nbrs)}, school_nbrs_standard: {len(self.school_nbrs_standard)}, " \
              + f"school_nbrs_split: {len(self.school_nbrs_split[0])} {len(self.school_nbrs_split[1])}, office_nbrs: {len(self.office_nbrs)}")

        if print_progress:
            print("the following information represents the number of nodes per round for:")
            print("round:  [state_0, state_1, state_2, state_3, state_4, state_5, state_6]" \
                  + "  [infec_family, infec_school, infec_office, infec_children, infec_parents, immunized_detect, immunized_test]")

        num_infec_per_rnd = []
        states_per_rnd = []
        info_per_rnd = []

        for rnd in range(sim_iters):
            weekday = rnd + start_weekday % 7
            self.infec_nodes = {node for node, state in self.node_states.items() if state in [1, 2, 3, 4, 5]}
            self.spreading_parent_nodes = {node for node, state in self.node_states.items() if state in [4, 5] and node in self.office_nbrs}
            self.spreading_child_nodes = {node for node, state in self.node_states.items() if state in [4, 5] and (
                                          node in self.school_nbrs_standard \
                                          or node in self.school_nbrs_split[0] \
                                          or node in self.school_nbrs_split[1])}
            self.spreading_child_nodes_standard = {node for node in self.spreading_child_nodes if node in self.school_nbrs_standard}

            # spread in family every day
            infec_family_children = self.spread(self.family_nbrs, self.spreading_child_nodes, p_spread_family)
            infec_family_parents = self.spread(self.family_nbrs, self.spreading_parent_nodes, p_spread_family)

            # children are tested on monday morning and if they test positive, them and their families get quarantined
            immunized_monday_test = set()
            if weekday == 0:
                pos_tested_child_nodes = self.immunize_after_testing(self.spreading_child_nodes, p_testing)
                immunized_family_nbrs = self.immunize_family_nbrs(pos_tested_child_nodes, prob=1.0)
                immunized_monday_test = pos_tested_child_nodes.union(immunized_family_nbrs)

            # on wednesday children in non-split classes get tested
            immunized_wednesday_test = set()
            if weekday == 2:
                pos_tested_child_nodes = self.immunize_after_testing(self.spreading_child_nodes_standard, p_testing)
                immunized_family_nbrs = self.immunize_family_nbrs(pos_tested_child_nodes, prob=1.0)
                immunized_wednesday_test = pos_tested_child_nodes.union(immunized_family_nbrs) 

            # spread in office and school only during weekdays
            infec_office = set()
            infec_school_standard = set()
            infec_school_split = set()
            immunized_detect_standard = set()
            immunized_detect_split = set()
            if weekday in [0, 1, 2, 3, 4]:
                # spread in office
                infec_office = self.spread(self.office_nbrs, self.spreading_parent_nodes, p_spread_office)
                # with p_detect_parent an infection of a parent gets detected (shows symtoms) and its family gets quarantined
                immunized_detect_office = self.immunize_family_nbrs(infec_office, p_detect_parent)

                # handle standard classes
                if len(self.school_nbrs_standard) > 0:
                    infec_school_standard = self.spread(self.school_nbrs_standard, self.spreading_child_nodes, p_spread_school)
                    # with p_detect_child an infection of a child gets detected (shows symtoms) and its family gets quarantined
                    immunized_detect_standard = self.immunize_family_nbrs(infec_school_standard, p_detect_child)

                # handle alternating split classes
                if len(self.school_nbrs_split[0]) > 0:
                    current_class = rnd % 2
                    infec_school_split = self.spread(self.school_nbrs_split[current_class], self.spreading_child_nodes, p_spread_school)
                    immunized_detect_split = self.immunize_family_nbrs(infec_school_split, p_detect_child)

            # all infected nodes increase their state every round
            for infec_node in self.infec_nodes:
                self.node_states[infec_node] += 1

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
                'immunized_detect': len(immunized_detect_office) + len(immunized_detect_standard) + len(immunized_detect_split),
                'immunized_test': len(immunized_monday_test) + len(immunized_wednesday_test)})
            if print_progress:
                print(f"{rnd}:\t{states_per_rnd[rnd]}\t{list(info_per_rnd[rnd].values())}")

            num_infec = sum(states_per_rnd[rnd][1:])
            num_infec_per_rnd.append(num_infec)

        print(f"infected nodes: {num_infec}\n")
        if export_csv:
            self.write_csv(export_csv, states_per_rnd, info_per_rnd)
        return num_infec_per_rnd
