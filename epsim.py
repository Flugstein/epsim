# Agent based epidemic simulation modeling households, schools, offices and leisure/shopping activities.
# Agent states: suceptible, exposed, infectious, recovered.

import sys
import random
import math
from pathlib import Path


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
    def __init__(self, loc_type, tag, x, y, sqm):
        self.loc_type = loc_type
        self.tag = tag
        self.x = x
        self.y = y
        self.sqm = sqm
        self.infec_minutes = 0
        self.visits = []


    def register_visit(self, e, agent_id):
        visit_time = e.avg_visit_times[self.loc_type]
        visit_prob = e.need_minutes[self.loc_type] / (visit_time * 7)  # minutes per week / (average visit time * days in the week)

        if random.random() < visit_prob:
            if agent_id in e.quarantined.keys():
                return
            if agent_id in e.agents_in_state[0]:
                self.visits.append((agent_id, visit_time))
                return
            infectious_agent = False
            for s in e.states_infectious:
                infectious_agent |= agent_id in e.agents_in_state[s]
            if infectious_agent:
                self.infec_minutes += visit_time
                return


    def spread(self, e):
        minutes_opened = 12*60

        # e.loc_infec_rate: infection rate for 1 infectious person, and 1 susceptible person within 13sqm for 8h
        # "1.0" is a place holder for visit[1] (visited minutes)
        base_rate = e.contact_mult[self.loc_type] * (e.loc_infec_rate / (8*60/13)) * (1.0 / minutes_opened) * (self.infec_minutes / self.sqm)

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
    def __init__(self, household_nbrs, school_nbrs_standard, school_nbrs_split, office_nbrs, interhousehold_nbrs):
        self.agents_in_state = []
        self.household_nbrs = household_nbrs
        self.school_nbrs_standard = school_nbrs_standard
        self.school_nbrs_split = school_nbrs_split
        self.office_nbrs = office_nbrs
        self.interhousehold_nbrs = interhousehold_nbrs
        self.households = self.determine_clusters(self.household_nbrs)
        print(f"household_nbrs: {len(self.household_nbrs)}, school_nbrs_standard: {len(self.school_nbrs_standard)}, " \
              + f"school_nbrs_split: {len(self.school_nbrs_split[0])} {len(self.school_nbrs_split[1])}, "\
              + f"office_nbrs: {len(self.office_nbrs)}, households: {len(self.households)}")
        self.locations = {'supermarket': [], 'shop': [], 'restaurant': [], 'leisure': [], 'nightlife': []}  # locations of location type
        self.house_households = []  # households of houses
        self.house_visit_locs = []  # visit locations of location type of house


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
        self.infectious_adult_agents.discard(agent)
        self.infectious_child_agents.discard(agent)
        self.infectious_child_agents_standard.discard(agent)
        self.infectious_interhousehold_child_agents.discard(agent)
        self.infectious_interhousehold_adult_agents.discard(agent)


    def quarantine_agents_with_household(self, agents):
        quarantined_agents = set()
        for agent in agents:
            self.quarantine_agent(agent)
            quarantined_agents.add(agent)
            for nbr in self.household_nbrs[agent]:
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

    
    def is_adult_agent(self, agent):
        return agent in self.office_nbrs


    def is_child_agent(self, agent):
        return agent in self.school_nbrs_standard or agent in self.school_nbrs_split[0] or agent in self.school_nbrs_split[1]


    def run_sim(self, sim_iters, num_start_agents, perc_immune_agents, start_weekday, p_spread_household_dict, p_spread_school_dict,
                p_spread_office_dict, p_detect_child_dict, p_detect_adult_dict, testing_dict, omicron, split_stay_home,
                loc_infec_rate, avg_visit_times, need_minutes, contact_mult, p_interhh_visit_dict, print_progress=False):
        """
        Run the epidemic simulation with the given parameters.

        sim_iters               -- number of iterations/rounds to simulate
        num_start_agents        -- number of initially infecteded agents
                                   single value: agents get disributed equally over all states
                                   list: exact number of agents per state
        perc_immune_agents      -- percentage of initially immune agents
                                   single value: agents are randomly chosen
                                   dict: percentage of agents per agent class (households, adults, children)
        start_weekday           -- simulation start weekday (0: Monday, 1: Tuesday, ..., 6: Sunday)
        p_spread_household_dict -- probability to spread the infection within the household
        p_spread_school_dict    -- probability to spread the infection within the school
        p_spread_office_dict    -- probability to spread the infection within the office
        p_detect_child_dict     -- probability that an infected child gets detected and quarantined because of its symtoms
        p_detect_adult_dict     -- probability that an infected adult gets detected and quarantined because of its symtoms
        testing_dict            -- dict of type of test with probability that a test detects an infected person and weekday it is taken
                                   example: testing={'pcr': {'p': 0.95, 'weekdays': [2]}, 'antigen': {'p': 0.5, 'weekdays': [0, 4]}}
        omicron                 -- enable omicron variant (lower incubation time)
        split_stay_home         -- True: the two halfs of split classes don't alternate, but one half always stays home
        loc_infec_rate          -- infection rate for locations
        avg_visit_times         -- avg time an agent spends time at a location per visit
        need_minutes            -- personal needs in minutes per week
        contact_mult            -- infection rate multiplier per location
        p_interhh_visit_dict    -- probability for a person to visit their interhousehold family
        print_progress          -- print simulation statistics every round onto the console
        """

        # input conversion
        if isinstance(perc_immune_agents, tuple): perc_immune_agents = tuple2dict(perc_immune_agents, 1)
        if isinstance(p_spread_household_dict, tuple): p_spread_household_dict = tuple2dict(p_spread_household_dict, 1)
        if isinstance(p_spread_school_dict, tuple): p_spread_school_dict = tuple2dict(p_spread_school_dict, 1)
        if isinstance(p_spread_office_dict, tuple): p_spread_office_dict = tuple2dict(p_spread_office_dict, 1)
        if isinstance(p_detect_child_dict, tuple): p_detect_child_dict = tuple2dict(p_detect_child_dict, 1)
        if isinstance(p_detect_adult_dict, tuple): p_detect_adult_dict = tuple2dict(p_detect_adult_dict, 1)
        if isinstance(testing_dict, tuple): testing_dict = tuple2dict(testing_dict, 3)
        if isinstance(loc_infec_rate, tuple): loc_infec_rate = tuple2dict(loc_infec_rate, 1)
        if isinstance(avg_visit_times, tuple): avg_visit_times = tuple2dict(avg_visit_times, 1)
        if isinstance(need_minutes, tuple): need_minutes = tuple2dict(need_minutes, 1)
        if isinstance(contact_mult, tuple): contact_mult = tuple2dict(contact_mult, 1)
        if isinstance(p_interhh_visit_dict, tuple): p_interhh_visit_dict = tuple2dict(p_interhh_visit_dict, 1)

        if 0 not in p_spread_household_dict: raise ValueError("p_spread_household_dict must cointain value for round 0")
        if 0 not in p_spread_school_dict: raise ValueError("p_spread_school_dict must cointain value for round 0")
        if 0 not in p_spread_office_dict: raise ValueError("p_spread_office_dict must cointain value for round 0")
        if 0 not in p_detect_child_dict: raise ValueError("p_detect_child_dict must cointain value for round 0")
        if 0 not in p_detect_adult_dict: raise ValueError("p_detect_adult_dict must cointain value for round 0")
        if 0 not in p_interhh_visit_dict: raise ValueError("p_interhh_visit_dict must cointain value for round 0")
        if 0 not in testing_dict: raise ValueError("testing_dict must cointain value for round 0")

        self.agents_in_state = []
        self.agents_in_state.append({agent for agent in self.household_nbrs.keys()})
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

        self.loc_infec_rate = loc_infec_rate
        self.avg_visit_times = avg_visit_times
        self.need_minutes = need_minutes
        self.contact_mult = contact_mult

        # set immune agents
        children = list(self.school_nbrs_standard.keys()) + list(self.school_nbrs_split[0].keys()) + list(self.school_nbrs_split[1].keys())
        adults = list(self.office_nbrs.keys())
        if isinstance(perc_immune_agents, float):
            for agent in random.sample(self.agents_in_state[0], int(perc_immune_agents * n)):
                self.agents_in_state[0].remove(agent)
        elif isinstance(perc_immune_agents, dict):
            if 'households' in perc_immune_agents:
                immune_households = random.sample(self.households, int(perc_immune_agents['households'] * len(self.households)))
                for cluster in immune_households:
                    for agent in cluster:
                        self.agents_in_state[0].remove(agent)
            if 'adults' in perc_immune_agents:
                immune_adults = random.sample(adults, int(perc_immune_agents['adults'] * len(adults)))
                for agent in immune_adults:
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
        if not isinstance(num_start_agents, list) and len(num_start_agents) != self.num_agent_states - 2:  # w/o suceptible and immune
            raise ValueError("num_start_agents has wrong format")
        for s, num_agents in enumerate(num_start_agents, 1):
            for agent in random.sample(self.agents_in_state[0], num_agents):
                self.agents_in_state[0].remove(agent)
                self.agents_in_state[s].add(agent)

        # print simulation info
        print(f"starting simulation with n={n}, num_start_agents={num_start_agents}, perc_immune_agents={perc_immune_agents}, " \
              + f"start_weekday={start_weekday}, sim_iters={sim_iters}, " + f"p_spread_household_dict={p_spread_household_dict}, " \
              + f"p_spread_school_dict={p_spread_school_dict}, p_spread_office={p_spread_office_dict}, " \
              + f"p_detect_child_dict={p_detect_child_dict}, p_detect_adult_dict={p_detect_adult_dict}, testing_dict={testing_dict}")
        print(f"start immune: {num_start_immune}")

        if print_progress:
            print("the following information represents the number of agents per round for:")
            print("[(states), infected, infected_in_household, infected_in_school, infected_in_office, infected_in_interhousehold, " \
                  "infected_by_children, infected_by_adults, quarantined_by_detection, quarantined_by_test, infected_in_location]")

        # initialize simulation variables
        num_state_infected_and_immune_per_rnd = []
        info_per_rnd = []
        self.quarantined = {}

        # run simulation
        for rnd in range(sim_iters):
            weekday = (rnd + start_weekday) % 7

            if rnd in p_spread_household_dict: p_spread_household = p_spread_household_dict[rnd]
            if rnd in p_spread_office_dict: p_spread_office = p_spread_office_dict[rnd]
            if rnd in p_spread_school_dict: p_spread_school = p_spread_school_dict[rnd]
            if rnd in p_detect_child_dict: p_detect_child = p_detect_child_dict[rnd]
            if rnd in p_detect_adult_dict: p_detect_adult = p_detect_adult_dict[rnd]
            if rnd in testing_dict: testing = testing_dict[rnd]
            if rnd in p_interhh_visit_dict: p_interhh_visit = p_interhh_visit_dict[rnd]

            # info tracking: number of agents per state at beginning of the day
            num_agents_per_state = [len(agents) for agents in self.agents_in_state]
            num_agents_per_state.append(n - sum(num_agents_per_state))

            # end simulation when no new infections can occur anymore
            sim_end = True
            for s in (self.states_infectious | self.states_exposed):
                sim_end &= num_agents_per_state[s] == 0
            if sim_end:
                info = {
                    'states': tuple(num_agents_per_state[s] for s in range(self.num_agent_states)),
                    'infected': 0,
                    'infected_in_household': 0,
                    'infected_in_school': 0,
                    'infected_in_office': 0,
                    'infected_in_interhousehold': 0,
                    'infected_by_children': 0,
                    'infected_children': 0,
                    'infected_by_adults': 0,
                    'infected_adults': 0,
                    'quarantined_by_detection': 0,
                    'quarantined_by_test': 0,
                    'infected_in_supermarket': 0,
                    'infected_in_shop': 0,
                    'infected_in_restaurant': 0,
                    'infected_in_leisure': 0,
                    'infected_in_nightlife': 0
                }
                for i in range(rnd, sim_iters):
                    info_per_rnd.append(info)
                break

            self.visiting_relatives = {node for node in self.interhousehold_nbrs.keys() if random.random() < p_interhh_visit}

            # compute infectious agents for this round
            self.infectious_agents = set()
            for s in self.states_infectious:
                self.infectious_agents |= self.agents_in_state[s]
            self.infectious_adult_agents = self.infectious_agents & self.office_nbrs.keys()
            self.infectious_child_agents = self.infectious_agents & (self.school_nbrs_standard.keys() | self.school_nbrs_split[0].keys() \
                                                                     | self.school_nbrs_split[1].keys())
            self.infectious_child_agents_standard = self.infectious_child_agents & self.school_nbrs_standard.keys()
            self.infectious_interhousehold_child_agents = self.infectious_child_agents & self.visiting_relatives
            self.infectious_interhousehold_adult_agents = self.infectious_adult_agents & self.visiting_relatives

            # agents in quarantine for 10 rounds get released
            self.quarantined = {agent: counter for (agent, counter) in self.quarantined.items() if counter < 10}

            # split between quarantined and non-quarantined infectious agents
            self.quarantined_infectious_adult_agents = self.quarantined.keys() & self.infectious_adult_agents
            self.quarantined_infectious_child_agents = self.quarantined.keys() & self.infectious_child_agents
            self.infectious_adult_agents = self.infectious_adult_agents - self.quarantined.keys()
            self.infectious_child_agents = self.infectious_child_agents - self.quarantined.keys()
            self.infectious_child_agents_standard = self.infectious_child_agents_standard - self.quarantined.keys()
            self.infectious_interhousehold_child_agents = self.infectious_interhousehold_child_agents - self.quarantined.keys()
            self.infectious_interhousehold_adult_agents = self.infectious_interhousehold_adult_agents - self.quarantined.keys()

            # spreading, testing and detection
            # spread in household (quarantined agents only spread in household)
            infected_in_household_by_children = self.spread(self.household_nbrs, self.quarantined_infectious_child_agents, p_spread_household)
            infected_in_household_by_adults = self.spread(self.household_nbrs, self.quarantined_infectious_adult_agents, p_spread_household)

            infected_in_household_by_children |= self.spread(self.household_nbrs, self.infectious_child_agents, p_spread_household)
            infected_in_household_by_adults |= self.spread(self.household_nbrs, self.infectious_adult_agents, p_spread_household)

            infected_in_household = infected_in_household_by_children | infected_in_household_by_adults

            # test children on monday, wednesday and friday and if they test positive, them and their households get quarantined
            quarantined_by_test = set()
            for testing_type, testing_params in testing.items():
                if weekday in testing_params['weekdays']:
                    if omicron and testing_type == 'pcr':
                        pos_tested_children = self.test_agents(self.infectious_child_agents & self.agents_in_state[2], testing_params['p'])
                    else:
                        pos_tested_children = self.test_agents(self.infectious_child_agents, testing_params['p'])
                    quarantined_by_test = self.quarantine_agents_with_household(pos_tested_children)

            # spread in office only during weekdays
            infected_in_office = set()
            quarantined_by_detection_in_office = set()
            if weekday in [0, 1, 2, 3, 4]:
                infected_in_office = self.spread(self.office_nbrs, self.infectious_adult_agents, p_spread_office)
                # with p_detect_adult an infection of a adult gets detected (shows symtoms) and it and its household gets quarantined
                detected_in_office = self.detect_agents(infected_in_office, p_detect_adult)
                quarantined_by_detection_in_office = self.quarantine_agents_with_household(detected_in_office)

            # spread in school only during weekdays
            infeced_in_school_standard = set()
            infected_in_school_split = set()
            quarantined_by_detection_in_school_standard = set()
            quarantined_by_detection_in_school_split = set()
            if weekday in [0, 1, 2, 3, 4]:
                # handle standard classes
                if len(self.school_nbrs_standard) > 0:
                    infeced_in_school_standard = self.spread(self.school_nbrs_standard, self.infectious_child_agents, p_spread_school)
                    # with p_detect_child an infection of a child gets detected (shows symtoms) and it and its household gets quarantined
                    detected_in_school_standard = self.detect_agents(infeced_in_school_standard, p_detect_child)
                    quarantined_by_detection_in_school_standard = self.quarantine_agents_with_household(detected_in_school_standard)

                # handle alternating split classes
                if len(self.school_nbrs_split[0]) > 0:
                    if split_stay_home:
                        current_half = 0  # half 0 always goes to school, while half 1 stays home
                    else:
                        current_half = rnd % 2  # alternate halfs of class
                    infected_in_school_split = self.spread(self.school_nbrs_split[current_half], self.infectious_child_agents, 
                                                           p_spread_school)
                    detected_in_school_split = self.detect_agents(infected_in_school_split, p_detect_child)
                    quarantined_by_detection_in_school_split = self.quarantine_agents_with_household(detected_in_school_split)

            infected_in_school = infeced_in_school_standard | infected_in_school_split
            quarantined_by_detection_in_school = quarantined_by_detection_in_school_standard | quarantined_by_detection_in_school_split

            # spread in interhouseholds (visits to relatives) only once every 30 days
            infected_in_interhousehold_by_children = self.spread(self.interhousehold_nbrs, self.infectious_interhousehold_child_agents, p_spread_household)
            infected_in_interhousehold_by_adults = self.spread(self.interhousehold_nbrs, self.infectious_interhousehold_adult_agents, p_spread_household)
            infected_in_interhousehold = infected_in_interhousehold_by_children | infected_in_interhousehold_by_adults

            # register visits
            for h, house in enumerate(self.house_households):
                for loc_type, visit_locs in self.house_visit_locs[h].items():
                    for hh in house:
                        for agent in self.households[hh]:
                            visit_loc = random.choice(visit_locs)  # pick random location from favourite locations
                            visit_loc.register_visit(self, agent)

            # spread in locations
            infected_in_location = {}
            for loc_type, locs in self.locations.items():
                infected_in_location[loc_type] = set()
                for loc in locs:
                    infected_in_location[loc_type] |= loc.spread(self)

            infected_by_children = infected_in_household_by_children | infected_in_interhousehold_by_children | infected_in_school  # does not count infections in locations
            infected_by_adults = infected_in_household_by_adults | infected_in_interhousehold_by_adults | infected_in_office  # does not count infections in locations
            infected = infected_by_children | infected_by_adults
            for loc_type, infec_in_loc in infected_in_location.items():
                infected |= infec_in_loc
            quarantined_by_detection = quarantined_by_detection_in_office | quarantined_by_detection_in_school
            infected_children = {agent for agent in infected if self.is_child_agent(agent)}
            infected_adults = {agent for agent in infected if self.is_adult_agent(agent)}

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
                'infected_in_household': len(infected_in_household),
                'infected_in_school': len(infected_in_school),
                'infected_in_office': len(infected_in_office),
                'infected_in_interhousehold': len(infected_in_interhousehold),
                'infected_by_children': len(infected_by_children),
                'infected_children': len(infected_children),
                'infected_by_adults': len(infected_by_adults),
                'infected_adults': len(infected_adults),
                'quarantined_by_detection': len(quarantined_by_detection),
                'quarantined_by_test': len(quarantined_by_test),
                'infected_in_supermarket': len(infected_in_location['supermarket']),
                'infected_in_shop': len(infected_in_location['shop']),
                'infected_in_restaurant': len(infected_in_location['restaurant']),
                'infected_in_leisure': len(infected_in_location['leisure']),
                'infected_in_nightlife': len(infected_in_location['nightlife'])
            }
            info_per_rnd.append(info)
            if print_progress:
                print(f"{rnd}:\t{list(info.values())}")

        total_infected = sum(info_per_rnd[-1]['states'][1:])
        print(f"infected: {total_infected}")
        print()
        return info_per_rnd
