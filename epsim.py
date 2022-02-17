import sys
import random
import math
from pathlib import Path

avg_visit_times = {'park': 90, 'leisure': 60, 'shopping': 60, 'supermarket': 60}  # average time spent per visit
contact_rate_multipliers = {'park': 0.25, 'leisure': 0.25, 'shopping': 0.25, 'supermarket': 0.25}
need_minutes = {'park': 74, 'leisure': 600, 'shopping': 98, 'supermarket': 60}  # personal needs in minutes per week
infection_rate = 0.07

def chunks(lst, n):
    """Yield successive n-sized chunks from lst"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


class Location:
    def __init__(self, loc_type, x, y, sqm):
        self.loc_type = loc_type
        self.x = x
        self.y = y
        self.sqm = sqm
        self.infec_minutes = 0

        if self.loc_type == 'park':
            self.sqm *= 10 # https://www.medrxiv.org/content/10.1101/2020.02.28.20029272v2 (I took a factor of 10 instead of 19 due to the large error bars)
        
        self.visits = []
        self.visit_time = avg_visit_times[self.loc_type]
        self.visit_prob = need_minutes[self.loc_type] / (self.visit_time * 7) # = minutes per week / (average visit time * days in the week)


    def register_visit(self, e, node_id):
        if random.random() < self.visit_prob:
            if node_id in e.quarantined.keys():
                return
            if node_id in e.nodes_in_state[0]:
                self.visits.append((node_id, self.visit_time))
                return
            spreading_node = False
            for s in e.states_spreading:
                spreading_node |= node_id in e.nodes_in_state[s]
            if spreading_node:
                self.infec_minutes += self.visit_time
                return


    def spread(self, e):
        minutes_opened = 12*60

        base_rate = contact_rate_multipliers[self.loc_type] * (infection_rate / 360.0) * (1.0 / minutes_opened) * (self.infec_minutes / self.sqm)
        # For Covid-19 this should be 0.07 (infection rate) for 1 infectious person, and 1 susceptible person within 2m for a full day.
        # I assume they can do this in a 4m^2 area.
        # So 0.07 = x * (24*60/24*60) * (24*60/4) -> 0.07 = x * 360 -> x = 0.07/360 = 0.0002
        # "1.0" is a place holder for v[1] (visited minutes).

        infected_nodes = set()
        for visit in self.visits:
            node = visit[0]
            if node in e.nodes_in_state[0]:
                infec_prob = visit[1] * base_rate
                if random.random() < infec_prob:
                    e.nodes_in_state[0].remove(node)
                    infected_nodes.add(node)
        
        # clear for next round
        self.visits = []
        self.infec_minutes = 0
        return infected_nodes


class Epsim:
    def __init__(self, family_nbrs, school_nbrs_standard, school_nbrs_split, office_nbrs):
        self.nodes_in_state = []
        self.family_nbrs = family_nbrs
        self.school_nbrs_standard = school_nbrs_standard
        self.school_nbrs_split = school_nbrs_split
        self.office_nbrs = office_nbrs
        self.families = self.determine_clusters(self.family_nbrs)
        print(f"family_nbrs: {len(self.family_nbrs)}, school_nbrs_standard: {len(self.school_nbrs_standard)}, " \
              + f"school_nbrs_split: {len(self.school_nbrs_split[0])} {len(self.school_nbrs_split[1])}, office_nbrs: {len(self.office_nbrs)}, " \
              + f"families: {len(self.families)}")
        self.locations = {}  # locations of location type
        self.nearest_locs = [{} for family in self.families]  # nearest location of location type of family

    def spread(self, nbrs_dict, spreading_nodes, prob):
        infected_nodes = set()
        for spreading_node in spreading_nodes:
            if spreading_node in nbrs_dict:
                for nbr in nbrs_dict[spreading_node]:
                    if nbr in self.nodes_in_state[0]:
                        if random.random() < prob:
                            self.nodes_in_state[0].remove(nbr)
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
                p_detect_parent, testing, omicron=False, split_stay_home=False, print_progress=False):
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
        testing           -- dict of type of test with probability that a test detects an infected person and weekday it is taken
                             example: testing={'pcr': {'p': 0.95, 'weekdays': [2]}, 'antigen': {'p': 0.5, 'weekdays': [0, 4]}}
        omicron           -- enable omicron variant (lower incubation time)
        split_stay_home   -- True: the two halfs of split classes don't alternate, but one half always stays home
        print_progress    -- print simulation statistics every round onto the console
        """

        # input conversion
        if isinstance(perc_immune_nodes, tuple):
            perc_immune_nodes = dict(perc_immune_nodes)
        if isinstance(testing, tuple):
            testing = dict(testing)
            for key, value in testing.items():
                testing[key] = dict(value)

        self.nodes_in_state = []
        self.nodes_in_state.append({node for node in self.family_nbrs.keys()})
        n = len(self.nodes_in_state[0])

        # node states
        if omicron:
            self.num_node_states = 4
            self.states_incubation = set()
            self.states_spreading = {1, 2}
        else:
            self.num_node_states = 7
            self.states_incubation = {1, 2, 3}
            self.states_spreading = {4, 5}

        for i in range(1, self.num_node_states - 1):
            self.nodes_in_state.append(set())

        # set immune nodes
        children = list(self.school_nbrs_standard.keys()) + list(self.school_nbrs_split[0].keys()) + list(self.school_nbrs_split[1].keys())
        parents = list(self.office_nbrs.keys())
        if isinstance(perc_immune_nodes, float):
            for node in random.sample(self.nodes_in_state[0], int(perc_immune_nodes * n)):
                self.nodes_in_state[0].remove(node)
        elif isinstance(perc_immune_nodes, dict):
            if 'families' in perc_immune_nodes:
                immune_families = random.sample(self.families, int(perc_immune_nodes['families'] * len(self.families)))
                for cluster in immune_families:
                    for node in cluster:
                        self.nodes_in_state[0].remove(node)
            if 'parents' in perc_immune_nodes:
                immune_parents = random.sample(parents, int(perc_immune_nodes['parents'] * len(parents)))
                for node in immune_parents:
                    self.nodes_in_state[0].remove(node)
            if 'children' in perc_immune_nodes:
                immune_children = random.sample(children, int(perc_immune_nodes['children'] * len(children)))
                for node in immune_children:
                    self.nodes_in_state[0].remove(node)
        else:
            raise ValueError("perc_immune_nodes has wrong format")

        num_start_immune = n - len(self.nodes_in_state[0])
        
        # set starting nodes
        if isinstance(num_start_nodes, int):
            num_start_nodes = [int(num_start_nodes / (self.num_node_states - 2))] * (self.num_node_states - 2)
        if not isinstance(num_start_nodes, list) and len(num_start_nodes) != self.num_node_states - 2:  # without not infected and immune states
            raise ValueError("num_start_nodes has wrong format")
        for s, num_nodes in enumerate(num_start_nodes, 1):
            for node in random.sample(self.nodes_in_state[0], num_nodes):
                self.nodes_in_state[0].remove(node)
                self.nodes_in_state[s].add(node)

        # print simulation info
        print(f"starting simulation with n={n}, num_start_nodes={num_start_nodes}, perc_immune_nodes={perc_immune_nodes}, " \
              + f"start_weekday={start_weekday}, sim_iters={sim_iters}" + f"p_spread_family={p_spread_family}, p_spread_school={p_spread_school}," \
              + f"p_spread_office={p_spread_office}, p_detect_child={p_detect_child}, " \
              + f"p_detect_parent={p_detect_parent}, testing={testing}")
        print(f"start immune: {num_start_immune}")

        if print_progress:
            print("the following information represents the number of nodes per round for:")
            print("[(states), infected, infected_in_family, infected_in_school, infected_in_office, infected_by_children, infected_by_parents, " \
                  +"quarantined_by_detection, quarantined_by_test, infected_in_location]")

        # initialize simulation variables
        num_state_infected_and_immune_per_rnd = []
        info_per_rnd = []
        self.quarantined = {}

        # run simulation
        for rnd in range(sim_iters):
            weekday = (rnd + start_weekday) % 7

            # info tracking: number of nodes per state at beginning of the day
            num_nodes_per_state = [len(nodes) for nodes in self.nodes_in_state]
            num_nodes_per_state.append(n - sum(num_nodes_per_state))

            sim_end = True
            for s in (self.states_spreading | self.states_incubation):
                sim_end &= num_nodes_per_state[s] == 0
            if sim_end:
                print("SIM END")
                break

            # compute spreading nodes for this round
            self.spreading_nodes = set()
            for s in self.states_spreading:
                self.spreading_nodes |= self.nodes_in_state[s]
            self.spreading_parent_nodes = self.spreading_nodes & self.office_nbrs.keys()
            self.spreading_child_nodes = self.spreading_nodes \
                                         & (self.school_nbrs_standard.keys() | self.school_nbrs_split[0].keys() | self.school_nbrs_split[1].keys())
            self.spreading_child_nodes_standard = self.spreading_child_nodes & self.school_nbrs_standard.keys()

            # nodes in quarantine for 10 rounds get released
            self.quarantined = {node: counter for (node, counter) in self.quarantined.items() if counter < 10}

            # split between quarantined and non-quarantined spreading nodes
            self.quarantined_spreading_parent_nodes = self.quarantined.keys() & self.spreading_parent_nodes
            self.quarantined_spreading_child_nodes = self.quarantined.keys() & self.spreading_child_nodes
            self.spreading_parent_nodes = self.spreading_parent_nodes - self.quarantined.keys()
            self.spreading_child_nodes = self.spreading_child_nodes - self.quarantined.keys()
            self.spreading_child_nodes_standard = self.spreading_child_nodes_standard - self.quarantined.keys()

            # spreading, testing and detection
            # spread in family (quarantined nodes only spread in family)
            infected_in_family_by_children = self.spread(self.family_nbrs, self.quarantined_spreading_child_nodes, p_spread_family)
            infected_in_family_by_parents = self.spread(self.family_nbrs, self.quarantined_spreading_parent_nodes, p_spread_family)

            infected_in_family_by_children |= self.spread(self.family_nbrs, self.spreading_child_nodes, p_spread_family)
            infected_in_family_by_parents |= self.spread(self.family_nbrs, self.spreading_parent_nodes, p_spread_family)

            infected_in_family = infected_in_family_by_children | infected_in_family_by_parents

            # test children on monday, wednesday and friday and if they test positive, them and their families get quarantined
            quarantined_by_test = set()
            for testing_type, testing_params in testing.items():
                if weekday in testing_params['weekdays']:
                    if omicron and testing_type == 'pcr':
                        pos_tested_children = self.test_nodes(self.spreading_child_nodes & self.nodes_in_state[2], testing_params['p'])
                    else:
                        pos_tested_children = self.test_nodes(self.spreading_child_nodes, testing_params['p'])
                    quarantined_by_test = self.quarantine_nodes_with_family(pos_tested_children)

            # spread in office only during weekdays
            infected_in_office = set()
            quarantined_by_detection_in_office = set()
            if weekday in [0, 1, 2, 3, 4]:
                infected_in_office = self.spread(self.office_nbrs, self.spreading_parent_nodes, p_spread_office)
                # with p_detect_parent an infection of a parent gets detected (shows symtoms) and it and its family gets quarantined
                detected_in_office = self.detect_nodes(infected_in_office, p_detect_parent)
                quarantined_by_detection_in_office = self.quarantine_nodes_with_family(detected_in_office)

            # spread in school only during weekdays
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
                    if split_stay_home:
                        current_half = 0  # half 0 always goes to school, while half 1 stays home
                    else:
                        current_half = rnd % 2  # alternate halfs of class
                    infected_in_school_split = self.spread(self.school_nbrs_split[current_half], self.spreading_child_nodes, p_spread_school)
                    detected_in_school_split = self.detect_nodes(infected_in_school_split, p_detect_child)
                    quarantined_by_detection_in_school_split = self.quarantine_nodes_with_family(detected_in_school_split)

            infected_in_school = infeced_in_school_standard | infected_in_school_split
            quarantined_by_detection_in_school = quarantined_by_detection_in_school_standard | quarantined_by_detection_in_school_split

            # register visits
            for i, family in enumerate(self.families):
                for loc_type, loc in self.nearest_locs[i].items():
                    for node in family:
                        loc.register_visit(self, node)

            # spread in locations
            infected_in_location = {}
            for loc_type, locs in self.locations.items():
                infected_in_location[loc_type] = set()
                for loc in locs:
                    infected_in_location[loc_type] |= loc.spread(self)

            infected_by_children = infected_in_family_by_children | infected_in_school  # does not count infections in locations
            infected_by_parents = infected_in_family_by_parents | infected_in_office  # does not count infections in locations
            infected = infected_by_children | infected_by_parents
            for loc_type, infec_in_loc in infected_in_location.items():
                infected |= infec_in_loc
            quarantined_by_detection = quarantined_by_detection_in_office | quarantined_by_detection_in_school
            infected_children = {node for node in infected if self.is_child_node(node)}
            infected_parents = {node for node in infected if self.is_parent_node(node)}

            # all infected nodes increase their state every round, nodes in final state get removed
            for s in reversed(range(2, len(self.nodes_in_state))):
                self.nodes_in_state[s] = self.nodes_in_state[s - 1]
            self.nodes_in_state[1] = infected

            # increase quarantine counter for every quarantined node
            for quarantined_node in self.quarantined:
                self.quarantined[quarantined_node] += 1

            # info tracking: what happened during the day
            info = {
                'states': tuple(num_nodes_per_state[s] for s in range(self.num_node_states)),
                'infected': len(infected),
                'infected_in_family': len(infected_in_family),
                'infected_in_school': len(infected_in_school),
                'infected_in_office': len(infected_in_office),
                'infected_by_children': len(infected_by_children),
                'infected_children': len(infected_children),
                'infected_by_parents': len(infected_by_parents),
                'infected_parents': len(infected_parents),
                'quarantined_by_detection': len(quarantined_by_detection),
                'quarantined_by_test': len(quarantined_by_test),
                #'infected_in_location': tuple({loc_type: len(infec_in_loc) for loc_type, infec_in_loc in infected_in_location.items()})
                'infected_in_location': sum(len(infec_in_loc) for loc_type, infec_in_loc in infected_in_location.items())
            }
            info_per_rnd.append(info)
            if print_progress:
                print(f"{rnd}:\t{list(info.values())}")

        total_infected = sum(info_per_rnd[-1]['states'][1:])
        print(f"infected: {total_infected}")
        print()
        return info_per_rnd
