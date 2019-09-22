## Defines utility functions used to produce stable marriages
class Woman:
    def __init__(self, name, preference_list):
        self.suitor = None
        self.name = name
        self.preference_list = preference_list
        self.num_suitors = len(preference_list)

        # Construct a dictionary from the name of the man to the preference index
        d = {}
        for i, man in enumerate(preference_list):
            d[man] = i
        self.preference_dict = d

    def get_ranking(self, man):
        if man is None:
            return self.num_suitors
        return self.preference_dict[man]        

class Man:
    def __init__(self, name, preference_list):
        self.preference_list = preference_list
        self.num_candidates = len(preference_list)
        self.name = name
        self.next_index = 0

    def next_candidate(self):
        if self.next_index == self.num_candidates:
            return None
        woman = self.preference_list[self.next_index]
        self.next_index += 1
        return woman

def stable_marriage(male, female):
    """
    Performs Gayle-Shapely stable marriage (the SM problem).
    The length of male does not necessarily have to equal the length of female
    Assumes there is no member of either group who states that they prefer a non-existant member of the other group

    Parameters
    --------------------
    male: Dictionary in which the keys are names of men, and the values are the ordered list of their female preferences
    female: Dictionary in which the keys are names of women, and the values are the ordered list of their male preferences

    Returns
    --------------------
    List of tuples representing the marriages.
    Each element contains a pairing in (male, female) ordering
    """
    # proposed_to -> proposing
    marriages = {}

    # Dictionary from the name of a man to the corresponding Man object
    men_dict = {}
    for name, preference in list(male.items()):
        men_dict[name] = Man(name, preference)
    # Dictionary from the name of a woman to the corresponding Woman object
    women_dict = {}
    for name, preference in list(female.items()):
        women_dict[name] = Woman(name, preference)
    # List of all males who have females they can still propose to
    bachelors = []
    for name, preference in list(male.items()):
        bachelors.append(Man(name, preference))

    # This should be optimized to use deque over list and del
    # While there are still men that can propose
    while len(bachelors) > 0:
        bachelor = bachelors[0]
        del bachelors[0]

        woman_name = bachelor.next_candidate()
        # This man is out of women to propose to, no matching is possible anymore
        if woman_name is None:
            return []
        woman = women_dict[woman_name]

        while woman.get_ranking(bachelor.name) > woman.get_ranking(woman.suitor):
            woman_name = bachelor.next_candidate()
            if woman_name is None:
                return []
            woman = women_dict[woman_name]

        # woman now contains a woman who prefers the bachelor to her current suitor
        if woman.suitor is not None:
            bachelors.append(men_dict[woman.suitor])
        woman.suitor = bachelor.name

    marriages = {}
    for name, woman in women_dict.items():
        marriages[name] = woman.suitor

    return [(man, woman) for woman, man in marriages.items()]
