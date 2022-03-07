# Agent based epidemic simulation modeling families, schools, offices and leisure/shopping activities.
# Agent states: suceptible, exposed, infectious, recovered.

import sys
import random
import math
from pathlib import Path

avg_visit_times = {'shop': 60, 'supermarket': 60, 'restaurant': 60, 'leisure': 120}  # average time spent per visit
contact_rate_multipliers = {'shop': 0.25, 'supermarket': 0.25, 'restaurant': 0.25, 'leisure': 0.25}
need_minutes = {'shop': 90, 'supermarket': 60, 'restaurant': 60, 'leisure': 600}  # personal needs in minutes per week
infection_rate = 0.07


def chunks(lst, n):
    """Yield successive n-sized chunks from lst"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def tuple2dict(tpl, nestings):
    dct = dict(tpl)
    if nestings > 1:
        for k, v in dct.items():
            dct[k] = tuple2dict(v, nestings - 1)
    return dct


class Location:
    def __init__(self, loc_type, x, y, sqm):
        self.loc_type = loc_type
        self.x = x
        self.y = y
        self.sqm = sqm
        self.infec_minutes = 0
        self.visits = []
        self.visit_time = avg_visit_times[self.loc_type]
        self.visit_prob = need_minutes[self.loc_type] / (self.visit_time * 7) # = minutes per week / (average visit time * days in the week)


    def register_visit(self, e, agent_id):
        if random.random() < self.visit_prob:
            if agent_id in e.quarantined.keys():
                return
            if agent_id in e.agents_in_state[0]:
                self.visits.append((agent_id, self.visit_time))
                return
            infectious_agent = False
            for s in e.states_infectious:
                infectious_agent |= agent_id in e.agents_in_state[s]
            if infectious_agent:
                self.infec_minutes += self.visit_time
                return


    def spread(self, e):
        minutes_opened = 12*60
        base_rate = contact_rate_multipliers[self.loc_type] * (infection_rate / 360.0) * (1.0 / minutes_opened) * (self.infec_minutes / self.sqm)
        # For Covid-19 this should be 0.07 (infection rate) for 1 infectious person, and 1 susceptible person within 2m for a full day.
        # Assume they can do this in a 4m^2 area.
        # So 0.07 = x * (24*60/24*60) * (24*60/4) -> 0.07 = x * 360 -> x = 0.07/360 = 0.0002
        # "1.0" is a place holder for v[1] (visited minutes).

        infected_agents = set()
        for visit in self.visits:
            agent = visit[0]
            if agent in e.agents_in_state[0]:
                infec_prob = visit[1] * base_rate
                if random.random() < infec_prob:
                    e.agents_in_state[0].remove(agent)
                    infected_agents.add(agent)
        
        # clear for next round
        self.visits = []
        self.infec_minutes = 0

        return infected_agents


class Epsim:
    def __init__(self, family_nbrs, school_nbrs_standard, school_nbrs_split, office_nbrs):
        self.agents_in_state = []
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


    def spread(self, nbrs_dict, infectious_agents, prob):
        infected_agents = set()
        for infectious_agent in infectious_agents:
            if infectious_agent in nbrs_dict:
                for nbr in nbrs_dict[infectious_agent]:
                    if nbr in self.agents_in_state[0]:
                        if random.random() < prob:
                            self.agents_in_state[0].remove(nbr)
                            infected_agents.add(nbr)
        return infected_agents


    def test_agents(self, agents, prob):
        return {agent for agent in agents if random.random() < prob}


    def detect_agents(self, agents, prob):
        return {agent for agent in agents if random.random() < prob}


    def quarantine_agent(self, agent):
        self.quarantined[agent] = 0
        self.infectious_agents.discard(agent)
        self.infectious_parent_agents.discard(agent)
        self.infectious_child_agents.discard(agent)
        self.infectious_child_agents_standard.discard(agent)


    def quarantine_agents_with_family(self, agents):
        quarantined_agents = set()
        for agent in agents:
            self.quarantine_agent(agent)
            quarantined_agents.add(agent)
            for nbr in self.family_nbrs[agent]:
                self.quarantine_agent(nbr)
                quarantined_agents.add(nbr)
        return quarantined_agents

    
    def determine_clusters(self, nbrs_dict):
        clusters = []
        agents_to_skip = set()
        for agent, nbrs in nbrs_dict.items():
            if agent not in agents_to_skip:
                clusters.append(sorted([agent] + list(nbrs)))
                agents_to_skip.update(nbrs)
        return clusters

    
    def is_parent_agent(self, agent):
        return agent in self.office_nbrs


    def is_child_agent(self, agent):
        return agent in self.school_nbrs_standard or agent in self.school_nbrs_split[0] or agent in self.school_nbrs_split[1]


    def run_sim(self, sim_iters, num_start_agents, perc_immune_agents, start_weekday, p_spread_family_dict, p_spread_school_dict, p_spread_office_dict, 
                p_detect_child_dict, p_detect_parent_dict, testing_dict, omicron=False, split_stay_home=False, print_progress=False):
        """
        Run the epidemic simulation with the given parameters.

        sim_iters            -- number of iterations/rounds to simulate
        num_start_agents     -- number of initially infecteded agents
                                can be a single value, where the agents get disributed equally over all states, 
                                or a list with the exact number of agents per state
        perc_immune_agents   -- percentage of initially immune agents
                                can be a single value, where the agents are randomly chosen, or a dict with the percentage of agents per agent class
                                (families, parents, children)
        start_weekday        -- weekday to start the simulation with (0: Monday, 1: Tuesday, ..., 6: Sunday)
        p_spread_family_dict -- probability to spread the infection within the family
        p_spread_school_dict -- probability to spread the infection within the school
        p_spread_office_dict -- probability to spread the infection within the office
        p_detect_child_dict  -- probability that an infected child gets detected and quarantined because of its symtoms
        p_detect_parent_dict -- probability that an infected parent gets detected and quarantined because of its symtoms
        testing_dict         -- dict of type of test with probability that a test detects an infected person and weekday it is taken
                                example: testing={'pcr': {'p': 0.95, 'weekdays': [2]}, 'antigen': {'p': 0.5, 'weekdays': [0, 4]}}
        omicron              -- enable omicron variant (lower incubation time)
        split_stay_home      -- True: the two halfs of split classes don't alternate, but one half always stays home
        print_progress       -- print simulation statistics every round onto the console
        """

        # input conversion
        if isinstance(perc_immune_agents, tuple): perc_immune_agents = tuple2dict(perc_immune_agents, 1)
        if isinstance(p_spread_family_dict, tuple): p_spread_family_dict = tuple2dict(p_spread_family_dict, 1)
        if isinstance(p_spread_school_dict, tuple): p_spread_school_dict = tuple2dict(p_spread_school_dict, 1)
        if isinstance(p_spread_office_dict, tuple): p_spread_office_dict = tuple2dict(p_spread_office_dict, 1)
        if isinstance(p_detect_child_dict, tuple): p_detect_child_dict = tuple2dict(p_detect_child_dict, 1)
        if isinstance(p_detect_parent_dict, tuple): p_detect_parent_dict = tuple2dict(p_detect_parent_dict, 1)
        if isinstance(testing_dict, tuple): testing_dict = tuple2dict(testing_dict, 3)

        if 0 not in p_spread_family_dict: raise ValueError("p_spread_family_dict must cointain value for round 0")
        if 0 not in p_spread_school_dict: raise ValueError("p_spread_school_dict must cointain value for round 0")
        if 0 not in p_spread_office_dict: raise ValueError("p_spread_office_dict must cointain value for round 0")
        if 0 not in p_detect_child_dict: raise ValueError("p_detect_child_dict must cointain value for round 0")
        if 0 not in p_detect_parent_dict: raise ValueError("p_detect_parent_dict must cointain value for round 0")
        if 0 not in testing_dict: raise ValueError("testing_dict must cointain value for round 0")

        self.agents_in_state = []
        self.agents_in_state.append({agent for agent in self.family_nbrs.keys()})
        n = len(self.agents_in_state[0])

        # agent states
        if omicron:
            self.num_agent_states = 4
            self.states_exposed = set()
            self.states_infectious = {1, 2}
        else:
            self.num_agent_states = 7
            self.states_exposed = {1, 2, 3}
            self.states_infectious = {4, 5}

        for i in range(1, self.num_agent_states - 1):
            self.agents_in_state.append(set())

        # set immune agents
        children = list(self.school_nbrs_standard.keys()) + list(self.school_nbrs_split[0].keys()) + list(self.school_nbrs_split[1].keys())
        parents = list(self.office_nbrs.keys())
        if isinstance(perc_immune_agents, float):
            for agent in random.sample(self.agents_in_state[0], int(perc_immune_agents * n)):
                self.agents_in_state[0].remove(agent)
        elif isinstance(perc_immune_agents, dict):
            if 'families' in perc_immune_agents:
                immune_families = random.sample(self.families, int(perc_immune_agents['families'] * len(self.families)))
                for cluster in immune_families:
                    for agent in cluster:
                        self.agents_in_state[0].remove(agent)
            if 'parents' in perc_immune_agents:
                immune_parents = random.sample(parents, int(perc_immune_agents['parents'] * len(parents)))
                for agent in immune_parents:
                    self.agents_in_state[0].remove(agent)
            if 'children' in perc_immune_agents:
                immune_children = random.sample(children, int(perc_immune_agents['children'] * len(children)))
                for agent in immune_children:
                    self.agents_in_state[0].remove(agent)
        else:
            raise ValueError("perc_immune_agents has wrong format")

        num_start_immune = n - len(self.agents_in_state[0])
        
        # set starting agents
        if isinstance(num_start_agents, int):
            num_start_agents = [int(num_start_agents / (self.num_agent_states - 2))] * (self.num_agent_states - 2)
        if not isinstance(num_start_agents, list) and len(num_start_agents) != self.num_agent_states - 2:  # without not infected and immune states
            raise ValueError("num_start_agents has wrong format")
        for s, num_agents in enumerate(num_start_agents, 1):
            for agent in random.sample(self.agents_in_state[0], num_agents):
                self.agents_in_state[0].remove(agent)
                self.agents_in_state[s].add(agent)

        # print simulation info
        print(f"starting simulation with n={n}, num_start_agents={num_start_agents}, perc_immune_agents={perc_immune_agents}, " \
              + f"start_weekday={start_weekday}, sim_iters={sim_iters}, " + f"p_spread_family_dict={p_spread_family_dict}, " \
              + f"p_spread_school_dict={p_spread_school_dict}, p_spread_office={p_spread_office_dict}, p_detect_child_dict={p_detect_child_dict}, " \
              + f"p_detect_parent_dict={p_detect_parent_dict}, testing_dict={testing_dict}")
        print(f"start immune: {num_start_immune}")

        if print_progress:
            print("the following information represents the number of agents per round for:")
            print("[(states), infected, infected_in_family, infected_in_school, infected_in_office, infected_by_children, infected_by_parents, " \
                  +"quarantined_by_detection, quarantined_by_test, infected_in_location]")

        # initialize simulation variables
        num_state_infected_and_immune_per_rnd = []
        info_per_rnd = []
        self.quarantined = {}

        # run simulation
        for rnd in range(sim_iters):
            weekday = (rnd + start_weekday) % 7

            if rnd in p_spread_family_dict: p_spread_family = p_spread_family_dict[rnd]
            if rnd in p_spread_office_dict: p_spread_office = p_spread_office_dict[rnd]
            if rnd in p_spread_school_dict: p_spread_school = p_spread_school_dict[rnd]
            if rnd in p_detect_child_dict: p_detect_child = p_detect_child_dict[rnd]
            if rnd in p_detect_parent_dict: p_detect_parent = p_detect_parent_dict[rnd]
            if rnd in testing_dict: testing = testing_dict[rnd]

            # info tracking: number of agents per state at beginning of the day
            num_agents_per_state = [len(agents) for agents in self.agents_in_state]
            num_agents_per_state.append(n - sum(num_agents_per_state))

            # end simulation when no new infections can occur anymore
            sim_end = True
            for s in (self.states_infectious | self.states_exposed):
                sim_end &= num_agents_per_state[s] == 0
            if sim_end:
                break

            # compute infectious agents for this round
            self.infectious_agents = set()
            for s in self.states_infectious:
                self.infectious_agents |= self.agents_in_state[s]
            self.infectious_parent_agents = self.infectious_agents & self.office_nbrs.keys()
            self.infectious_child_agents = self.infectious_agents \
                                         & (self.school_nbrs_standard.keys() | self.school_nbrs_split[0].keys() | self.school_nbrs_split[1].keys())
            self.infectious_child_agents_standard = self.infectious_child_agents & self.school_nbrs_standard.keys()

            # agents in quarantine for 10 rounds get released
            self.quarantined = {agent: counter for (agent, counter) in self.quarantined.items() if counter < 10}

            # split between quarantined and non-quarantined infectious agents
            self.quarantined_infectious_parent_agents = self.quarantined.keys() & self.infectious_parent_agents
            self.quarantined_infectious_child_agents = self.quarantined.keys() & self.infectious_child_agents
            self.infectious_parent_agents = self.infectious_parent_agents - self.quarantined.keys()
            self.infectious_child_agents = self.infectious_child_agents - self.quarantined.keys()
            self.infectious_child_agents_standard = self.infectious_child_agents_standard - self.quarantined.keys()

            # spreading, testing and detection
            # spread in family (quarantined agents only spread in family)
            infected_in_family_by_children = self.spread(self.family_nbrs, self.quarantined_infectious_child_agents, p_spread_family)
            infected_in_family_by_parents = self.spread(self.family_nbrs, self.quarantined_infectious_parent_agents, p_spread_family)

            infected_in_family_by_children |= self.spread(self.family_nbrs, self.infectious_child_agents, p_spread_family)
            infected_in_family_by_parents |= self.spread(self.family_nbrs, self.infectious_parent_agents, p_spread_family)

            infected_in_family = infected_in_family_by_children | infected_in_family_by_parents

            # test children on monday, wednesday and friday and if they test positive, them and their families get quarantined
            quarantined_by_test = set()
            for testing_type, testing_params in testing.items():
                if weekday in testing_params['weekdays']:
                    if omicron and testing_type == 'pcr':
                        pos_tested_children = self.test_agents(self.infectious_child_agents & self.agents_in_state[2], testing_params['p'])
                    else:
                        pos_tested_children = self.test_agents(self.infectious_child_agents, testing_params['p'])
                    quarantined_by_test = self.quarantine_agents_with_family(pos_tested_children)

            # spread in office only during weekdays
            infected_in_office = set()
            quarantined_by_detection_in_office = set()
            if weekday in [0, 1, 2, 3, 4]:
                infected_in_office = self.spread(self.office_nbrs, self.infectious_parent_agents, p_spread_office)
                # with p_detect_parent an infection of a parent gets detected (shows symtoms) and it and its family gets quarantined
                detected_in_office = self.detect_agents(infected_in_office, p_detect_parent)
                quarantined_by_detection_in_office = self.quarantine_agents_with_family(detected_in_office)

            # spread in school only during weekdays
            infeced_in_school_standard = set()
            infected_in_school_split = set()
            quarantined_by_detection_in_school_standard = set()
            quarantined_by_detection_in_school_split = set()
            if weekday in [0, 1, 2, 3, 4]:
                # handle standard classes
                if len(self.school_nbrs_standard) > 0:
                    infeced_in_school_standard = self.spread(self.school_nbrs_standard, self.infectious_child_agents, p_spread_school)
                    # with p_detect_child an infection of a child gets detected (shows symtoms) and it and its family gets quarantined
                    detected_in_school_standard = self.detect_agents(infeced_in_school_standard, p_detect_child)
                    quarantined_by_detection_in_school_standard = self.quarantine_agents_with_family(detected_in_school_standard)

                # handle alternating split classes
                if len(self.school_nbrs_split[0]) > 0:
                    if split_stay_home:
                        current_half = 0  # half 0 always goes to school, while half 1 stays home
                    else:
                        current_half = rnd % 2  # alternate halfs of class
                    infected_in_school_split = self.spread(self.school_nbrs_split[current_half], self.infectious_child_agents, p_spread_school)
                    detected_in_school_split = self.detect_agents(infected_in_school_split, p_detect_child)
                    quarantined_by_detection_in_school_split = self.quarantine_agents_with_family(detected_in_school_split)

            infected_in_school = infeced_in_school_standard | infected_in_school_split
            quarantined_by_detection_in_school = quarantined_by_detection_in_school_standard | quarantined_by_detection_in_school_split

            # register visits
            for i, family in enumerate(self.families):
                for loc_type, loc in self.nearest_locs[i].items():
                    for agent in family:
                        loc.register_visit(self, agent)

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
            infected_children = {agent for agent in infected if self.is_child_agent(agent)}
            infected_parents = {agent for agent in infected if self.is_parent_agent(agent)}

            # all infected agents increase their state every round, agents in final state get removed
            for s in reversed(range(2, len(self.agents_in_state))):
                self.agents_in_state[s] = self.agents_in_state[s - 1]
            self.agents_in_state[1] = infected

            # increase quarantine counter for every quarantined agent
            for quarantined_agent in self.quarantined:
                self.quarantined[quarantined_agent] += 1

            # info tracking: what happened during the day
            info = {
                'states': tuple(num_agents_per_state[s] for s in range(self.num_agent_states)),
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
