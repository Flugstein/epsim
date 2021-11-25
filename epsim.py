import sys
import random
import math
from pathlib import Path

### node states ###
# 0 not infected
# 1 infected: incubation
# 2 infected: incubation
# 3 infected: incubation
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
        self.nodes_clean = set()
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
        self.nodes_clean = {node for node in family_nbrs.keys()}


    def init_from_files(self, family_nbrs_path, school_standard_path, school_split_0_path, school_split_1_path, office_nbrs_path):
        print('read nbrs files')
        self.read_nbrs_file(self.family_nbrs, family_nbrs_path)
        self.read_nbrs_file(self.office_nbrs, office_nbrs_path)
        self.nodes_clean = {node for node in self.family_nbrs.keys()}

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


    def spread(self, nbrs_dict, spreading_nodes, prob):
        infected_nodes = set()
        for spreading_node in spreading_nodes:
            if spreading_node in nbrs_dict:
                for nbr in nbrs_dict[spreading_node]:
                    if nbr in self.nodes_clean:
                        if random.random() < prob:
                            self.node_states[nbr] = 1
                            self.nodes_clean.remove(nbr)
                            infected_nodes.add(nbr)
        return infected_nodes


    def test_nodes(self, nodes, prob):
        return {node for node in nodes if random.random() < prob}


    def detect_nodes(self, nodes, prob):
        return {node for node in nodes if random.random() < prob}


    def quarantine_node(self, node):
        self.quarantined[node] = 0
        self.spreading_nodes.discard(node)
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

    
    def is_parent_node(self, node):
        return node in self.office_nbrs


    def is_child_node(self, node):
        return node in self.school_nbrs_standard or node in self.school_nbrs_split[0] or node in self.school_nbrs_split[1]


    def run_sim(self, sim_iters, num_start_nodes, perc_immune_nodes, start_weekday, p_spread_family, p_spread_school, p_spread_office, p_detect_child, 
                p_detect_parent, p_testing, print_progress=False):
        """
        Run the epidemic simulation with the given parameters.

        sim_iters         -- number of iterations/rounds to simulate
        num_start_nodes   -- number of initially infecteded nodes
                             can be a single value, where the nodes get disributed equally over all states, or a list with the exact number of nodes per state
        perc_immune_nodes -- percentage of initially immune nodes
                             can be a single value, where the nodes are randomly chosen, or a dict with the percentage of nodes per node class
                             (families, parents, children)
        start_weekday     -- weekday to start the simulation with (0: Monday, 1: Tuesday, ..., 6: Sunday)
        p_spread_family   -- probability to spread the infection within the family
        p_spread_school   -- probability to spread the infection within the school
        p_spread_office   -- probability to spread the infection within the office
        p_detect_child    -- probability that an infected child gets detected and quarantined because of its symtoms
        p_detect_parent   -- probability that an infected parent gets detected and quarantined because of its symtoms
        p_testing         -- probability that a test detects an infected person
                             dict of weekday (0 to 6) and test probability
        print_progress    -- print simulation statistics every round onto the console
        """

        # input conversion
        if isinstance(perc_immune_nodes, tuple):
            perc_immune_nodes = dict(perc_immune_nodes)
        if isinstance(p_testing, tuple):
            p_testing = dict(p_testing)

        n = len(self.nodes_clean)

        ## set immune nodes
        children = list(self.school_nbrs_standard.keys()) + list(self.school_nbrs_split[0].keys()) + list(self.school_nbrs_split[1].keys())
        parents = self.office_nbrs.keys()
        families = self.determine_clusters(self.family_nbrs)
        if isinstance(perc_immune_nodes, float):
            for node in random.sample(self.nodes_clean, int(perc_immune_nodes * n)):
                self.nodes_clean.remove(node)
        elif isinstance(perc_immune_nodes, dict):
            if 'families' in perc_immune_nodes:
                immune_families = random.sample(families, int(perc_immune_nodes['families'] * len(families)))
                for cluster in immune_families:
                    for node in cluster:
                        self.nodes_clean.remove(node)
            if 'parents' in perc_immune_nodes:
                immune_parents = random.sample(parents, int(perc_immune_nodes['parents'] * len(parents)))
                for node in immune_parents:
                    self.nodes_clean.remove(node)
            if 'children' in perc_immune_nodes:
                immune_children = random.sample(children, int(perc_immune_nodes['children'] * len(children)))
                for node in immune_children:
                    self.nodes_clean.remove(node)
        else:
            raise ValueError("perc_immune_nodes has wrong format")

        num_start_immune = n - len(self.nodes_clean)
        
        ## set starting nodes
        if isinstance(num_start_nodes, int):
            num_start_nodes = [int(num_start_nodes / 5)] * 5
        if not isinstance(num_start_nodes, list) and len(num_start_nodes) != num_node_states - 2:  # without not infected and immune states
            raise ValueError("num_start_nodes has wrong format")
        sampled_nodes = random.sample(self.nodes_clean, sum(num_start_nodes))
        start_nodes_per_state = [[sampled_nodes.pop() for i in range(num)] for num in num_start_nodes]
        for i, start_nodes in enumerate(start_nodes_per_state, 1):
            for node in start_nodes:
                self.node_states[node] = i
                self.nodes_clean.remove(node)

        # print simulation info
        print(f"starting simulation with n={n}, num_start_nodes={num_start_nodes}, perc_immune_nodes={perc_immune_nodes}, " \
              + f"start_weekday={start_weekday}, sim_iters={sim_iters}")
        print(f"p_spread_family={p_spread_family}, p_spread_school={p_spread_school}, p_spread_office={p_spread_office}, p_detect_child={p_detect_child}, " \
              + f"p_detect_parent={p_detect_parent}, p_testing={p_testing}")
        print(f"family_nbrs: {len(self.family_nbrs)}, school_nbrs_standard: {len(self.school_nbrs_standard)}, " \
              + f"school_nbrs_split: {len(self.school_nbrs_split[0])} {len(self.school_nbrs_split[1])}, office_nbrs: {len(self.office_nbrs)}")
        print(f"start immune: {num_start_immune}")

        if print_progress:
            print("the following information represents the number of nodes per round for:")
            print("round: [state_0, state_1, state_2, state_3, state_4, state_5, state_6, " \
                  + "infected, infected_in_family, infected_in_school, infected_in_office, infected_by_children, infected_by_parents, " \
                  +"quarantined_by_detection, quarantined_by_test]")

        # initialize simulation variables
        num_state_infected_and_immune_per_rnd = []
        info_per_rnd = []
        self.quarantined = {}

        # run simulation
        for rnd in range(sim_iters):
            weekday = (rnd + start_weekday) % 7

            # info tracking: number of nodes per state at beginning of the day
            num_nodes_per_state = [0] * num_node_states
            num_nodes_per_state[0] = len(self.nodes_clean)
            for state in self.node_states.values():
                num_nodes_per_state[state] += 1
            num_nodes_per_state[6] = n - sum(num_nodes_per_state)

            # compute spreading nodes for this round
            infected_state_nodes = {node for node, state in self.node_states.items() if state in [1, 2, 3, 4, 5]}
            self.spreading_nodes = {node for node, state in self.node_states.items() if state in [4, 5]}
            self.spreading_parent_nodes = self.spreading_nodes & self.office_nbrs.keys()
            self.spreading_child_nodes = self.spreading_nodes \
                                         & (self.school_nbrs_standard.keys() | self.school_nbrs_split[0].keys() | self.school_nbrs_split[1].keys())
            self.spreading_child_nodes_standard = self.spreading_child_nodes & self.school_nbrs_standard.keys()

            ## nodes in quarantine for 10 rounds get released
            self.quarantined = {node: counter for (node, counter) in self.quarantined.items() if counter < 10}

            ## split between quarantined and non-quarantined spreading nodes
            self.quarantined_spreading_parent_nodes = self.quarantined.keys() & self.spreading_parent_nodes
            self.quarantined_spreading_child_nodes = self.quarantined.keys() & self.spreading_child_nodes
            self.spreading_parent_nodes = self.spreading_parent_nodes - self.quarantined.keys()
            self.spreading_child_nodes = self.spreading_child_nodes - self.quarantined.keys()
            self.spreading_child_nodes_standard = self.spreading_child_nodes_standard - self.quarantined.keys()

            # spreading, testing and detection
            ## spread in family (quarantined nodes only spread in family)
            infected_in_family_by_children = self.spread(self.family_nbrs, self.quarantined_spreading_child_nodes, p_spread_family)
            infected_in_family_by_parents = self.spread(self.family_nbrs, self.quarantined_spreading_parent_nodes, p_spread_family)

            infected_in_family_by_children |= self.spread(self.family_nbrs, self.spreading_child_nodes, p_spread_family)
            infected_in_family_by_parents |= self.spread(self.family_nbrs, self.spreading_parent_nodes, p_spread_family)

            infected_in_family = infected_in_family_by_children | infected_in_family_by_parents

            ## test children on monday, wednesday and friday and if they test positive, them and their families get quarantined
            quarantined_by_test = set()
            if weekday in p_testing:
                pos_tested_children = self.test_nodes(self.spreading_child_nodes, p_testing[weekday])
                quarantined_by_test = self.quarantine_nodes_with_family(pos_tested_children)

            ## spread in office only during weekdays
            infected_in_office = set()
            quarantined_by_detection_in_office = set()
            if weekday in [0, 1, 2, 3, 4]:
                infected_in_office = self.spread(self.office_nbrs, self.spreading_parent_nodes, p_spread_office)
                # with p_detect_parent an infection of a parent gets detected (shows symtoms) and it and its family gets quarantined
                detected_in_office = self.detect_nodes(infected_in_office, p_detect_parent)
                quarantined_by_detection_in_office = self.quarantine_nodes_with_family(detected_in_office)

            ## spread in school only during weekdays
            infeced_in_school_standard = set()
            infected_in_school_split = set()
            quarantined_by_detection_in_school_standard = set()
            quarantined_by_detection_in_school_split = set()
            if weekday in [0, 1, 2, 3, 4]:
                # handle standard classes
                if len(self.school_nbrs_standard) > 0:
                    infeced_in_school_standard = self.spread(self.school_nbrs_standard, self.spreading_child_nodes, p_spread_school)
                    # with p_detect_child an infection of a child gets detected (shows symtoms) and it and its family gets quarantined
                    detected_in_school_standard = self.detect_nodes(infeced_in_school_standard, p_detect_child)
                    quarantined_by_detection_in_school_standard = self.quarantine_nodes_with_family(detected_in_school_standard)

                # handle alternating split classes
                if len(self.school_nbrs_split[0]) > 0:
                    current_class = rnd % 2
                    infected_in_school_split = self.spread(self.school_nbrs_split[current_class], self.spreading_child_nodes, p_spread_school)
                    detected_in_school_split = self.detect_nodes(infected_in_school_split, p_detect_child)
                    quarantined_by_detection_in_school_split = self.quarantine_nodes_with_family(detected_in_school_split)

            infected_in_school = infeced_in_school_standard | infected_in_school_split
            quarantined_by_detection_in_school = quarantined_by_detection_in_school_standard | quarantined_by_detection_in_school_split

            # all infected nodes increase their state every round
            for node in infected_state_nodes:
                self.node_states[node] += 1
                if self.node_states[node] == 6:
                    self.node_states.pop(node)
                
            # increase quarantine counter for every quarantined node
            for quarantined_node in self.quarantined:
                self.quarantined[quarantined_node] += 1

            # info tracking: what happened during the day
            infected_by_children = infected_in_family_by_children | infected_in_school
            infected_by_parents = infected_in_family_by_parents | infected_in_office
            infected = infected_by_children | infected_by_parents
            quarantined_by_detection = quarantined_by_detection_in_office | quarantined_by_detection_in_school
            infected_children = {node for node in infected if self.is_child_node(node)}
            infected_parents = {node for node in infected if self.is_parent_node(node)}

            info_per_rnd.append({
                'state_0': num_nodes_per_state[0],
                'state_1': num_nodes_per_state[1],
                'state_2': num_nodes_per_state[2],
                'state_3': num_nodes_per_state[3],
                'state_4': num_nodes_per_state[4],
                'state_5': num_nodes_per_state[5],
                'state_6': num_nodes_per_state[6],
                'infected': len(infected),
                'infected_in_family': len(infected_in_family),
                'infected_in_school': len(infected_in_school),
                'infected_in_office': len(infected_in_office),
                'infected_by_children': len(infected_by_children),
                'infected_children': len(infected_children),
                'infected_by_parents': len(infected_by_parents),
                'infected_parents': len(infected_parents),
                'quarantined_by_detection': len(quarantined_by_detection),
                'quarantined_by_test': len(quarantined_by_test)})
            if print_progress:
                print(f"{rnd}:\t{list(info_per_rnd[rnd].values())}")

        total_infected = info_per_rnd[-1]['state_1']+info_per_rnd[-1]['state_2']+info_per_rnd[-1]['state_3']+info_per_rnd[-1]['state_4'] \
                         +info_per_rnd[-1]['state_5']+info_per_rnd[-1]['state_6']
        print(f"infected: {total_infected}")
        print()
        return info_per_rnd
