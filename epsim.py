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


    def run_sim(self, sim_iters, num_start_nodes, num_immuinzed_nodes, p_spread_family, p_spread_school, p_spread_office, p_detect_child, p_detect_parent,
                p_testing, print_progress=False, export_csv=False):
        for node in self.node_states:
            self.node_states[node] = 0
        
        start_nodes_per_state = list(chunks(random.sample(self.node_states.keys(), num_start_nodes), int(num_start_nodes / 5)))
        for i, start_nodes in enumerate(start_nodes_per_state, 1):
            for node in start_nodes:
                self.node_states[node] = i

        for node in random.sample(self.node_states.keys(), num_immuinzed_nodes):
            self.node_states[node] = 6

        print(f"starting simulation with n={len(self.node_states)}, num_start_nodes={num_start_nodes}, num_immuinzed_nodes={num_immuinzed_nodes}, " \
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
            weekday = rnd % 7
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


if __name__ == '__main__':
    if not (13 <= len(sys.argv) <= 16):
        print("usage: python epsim.py sim_iters num_start_nodes num_immuinzed_nodes p_spread_family p_spread_school p_spread_office p_detect_child" \
              + " p_detect_parent p_testing family.nbrs office.nbrs out.csv [school_standard.nbrs] [school_split_0.nbrs school_split_1.nbrs]")
        print("specify either school_standard.nbrs or school_split.nbrs, or both")
        print("children in school_standard.nbrs visit school every day. children in school_split.nbrs visit school every other day, alternating.")
        quit()

    sim_iters = int(sys.argv[1])
    num_start_nodes = int(sys.argv[2])
    num_immuinzed_nodes = int(sys.argv[3])
    p_spread_family = float(sys.argv[4])
    p_spread_school = float(sys.argv[5])
    p_spread_office = float(sys.argv[6])
    p_detect_child = float(sys.argv[7])
    p_detect_parent = float(sys.argv[8])
    p_testing = float(sys.argv[9])
    family_nbrs_path = Path(sys.argv[10])
    office_nbrs_path = Path(sys.argv[11])
    out_path = Path(sys.argv[12])

    if len(sys.argv) == 14:
        school_standard = Path(sys.argv[13])
        school_split_0 = None
        school_split_1 = None
    elif len(sys.argv) == 15:
        school_standard = None
        school_split_0 = Path(sys.argv[13])
        school_split_1 = Path(sys.argv[14])
    else:
        school_standard = Path(sys.argv[13])
        school_split_0 = Path(sys.argv[14])
        school_split_1 = Path(sys.argv[15])

    epsim = Epsim()
    epsim.init_from_files(family_nbrs_path, school_standard, school_split_0, school_split_1, office_nbrs_path)
    num_infec_per_rnd = epsim.run_sim(sim_iters, num_start_nodes, num_immuinzed_nodes, p_spread_family, p_spread_school, p_spread_office,
                                      p_detect_child, p_detect_parent, p_testing)

    with open(out_path, 'w') as f:
        for i in range(len(num_infec_per_rnd)):
            f.write(f"{i}, {num_infec_per_rnd[i]}\n")
