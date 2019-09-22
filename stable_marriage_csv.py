################################################################################
### Imports
################################################################################
import argparse
import pandas as pd
import stable_matching

################################################################################
### Data I/O
################################################################################
def parse_arguments():
    """
    Parses command line arguments to determine which files to read

    Returns
    --------------------
    A namespace containing all arguments passed in through command line
    """
    parser = argparse.ArgumentParser("Utility script used to producing stable matches between mentors and candidates.")
    parser.add_argument('mentor_file', metavar = 'MENTOR_FILE', type = str,
        help = "CSV containing the preference lists submitted by the mentors")
    parser.add_argument('candidate_file', metavar = 'CANDIDATE_FILE', type = str,
        help = 'CSV containing the preference lists submitted by the candidates')
    parser.add_argument('-o', '--output', dest = 'output_file', action = 'store', 
        help = "location of the output file")
    parser.add_argument('-n', dest = "num_preferences", action = 'store', default = 5, type = int,
        help = "number of preferences for each to consider (default 5)")
    return parser.parse_args()

def read_dataframe_candidate(file_name, n):
    """
    Reads the candidate CSV at file_name into a pandas dataframe.

    Parameters
    --------------------
    file_name: String containing the name of the candidate CSV to read
    n: Number of preferences to read

    Returns
    --------------------
    Pandas dataframe containing the following columns:
        1. Candidate name
        2. Mentor choice 1
        3. Mentor choice 2
        ...
        n+1. Mentor choice n
        n+2. Candidate year
    """
    cols = ["Name"]
    cols.extend(["Mentor Choice {}".format(i + 1) for i in range(n)])
    cols.append("Year")
    return read_dataframe(file_name, cols)

def read_dataframe_mentor(file_name, n):
    """
    Reads the mentor CSV at file_name into a pandas dataframe.

    Parameters
    --------------------
    file_name: String containing the name of the mentor CSV to read
    n: Number of preferences to read

    Returns
    --------------------
    Pandas dataframe containing the following columns:
        1. Mentor name
        2. Candidate choice 1
        3. Candidate choice 2
        ...
        n+1. Candidate choice n
        n+2. Mentor year
    """
    cols = ["Name"]
    cols.extend(["Candidate Choice {}".format(i + 1) for i in range(n)])
    cols.append("Year")
    return read_dataframe(file_name, cols)

def read_dataframe(file_name, columns):
    """
    Reads the contents of the CSV at file_name into a pandas dataframe.
    Returns only the columns specified, so the contents of the other columns are removed

    Parameters
    --------------------
    file_name: String containing the name of the file to read
    columns: List of Strings representing which columns to pull

    Returns
    --------------------
    Pandas dataframes containing the specified columns of the specified dataframe
    """
    df = pd.read_csv(file_name, sep = ",")
    return df[columns]

################################################################################
### Data Conversion/Preprocessing
################################################################################
def list_to_dictionary(lst):
    """
    Converts the nested list into a dictionary in which the first element maps to a list of the remaining elements

    Parameters
    --------------------
    lst: Nested (2+ dimension) list to convert. Each element must have at least 1 element. 

    Returns
    --------------------
    Dictionary as described above
    """
    d = {}
    for row in lst:
        d[row[0]] = row[1:]
    return d

def remove_pairings(pairings, mentors, candidates):
    """
    Removes the preference lists of mentors and candidates that are matched in pairings from their corresponding lists.
    Removes references to these mentors and candidates as well in both preference lists.
    !! Modifies mentors and candidates directly !!

    Parameters
    --------------------
    pairings: List of (mentor, candidate) matchings
    mentors: List of the preference list of all mentors (mentor name is element 0 of each row)
    candidates: List of the preference list of all candidates (candidate name is element 0 of each row)

    Returns
    --------------------
    None

    Throws
    --------------------
    ValueError from validate_data
    """
    for mentor, candidate in pairings:
        for row in candidates:
            if row[0] == candidate:
                candidates.remove(row)
        for row in mentors:
            if row[0] == mentor:
                mentors.remove(row)

    validate_data(mentors, candidates)

def validate_data(mentors, candidates, mentors_years = None, candidates_years = None, verbose = False):
    """
    Checks a variety of preconditions to make sure that the data supplied by the students is valid, including:
    1. Candidate and mentor names are unique
    2. Each candidate or mentor specified by a mentor or candidate respectively exists
    (3). Each candidate or mentor specified by a mentor or candidate respectively is of an appropriate year
    If verbose is specified, then verbose output is dumped to stdout. This is designed to be used for the first call.
    If both mentors_years and candidates_years are specified, then check (3) above is also done.

    Parameters
    --------------------
    mentors: List of the preference list of all mentors (mentor name is element 0 of each row)
    candidates: List of the preference list of all candidates (candidate name is element 0 of each row)
    mentors_years: Dictionary mapping from mentor name to mentor year
    candidates_years: Dictionary mapping from candidate name to candidate year
    verbose: Boolean value representing if verbose output should be dumped to stdout

    Returns
    --------------------
    None

    Throws
    --------------------
    ValueError if a mentor or candidate name is not unique
    """
    # Get candidate names and mentor names
    candidate_names = set([x[0] for x in candidates])
    mentor_names = set([x[0] for x in mentors])
    check_year = (mentors_years is not None) and (candidates_years is not None)

    # Validation of data
    if len(candidates) != len(candidate_names):
        blank = set()
        bad_people = []
        for candidate in candidates:
            if candidate[0] in blank:
                bad_people.append(candidate[0])
            else:
                blank.add(candidate[0])
        raise ValueError("There were at least two candidates with the exact same name. Check {}".format(bad_people))

    if len(mentors) != len(mentor_names):
        blank = set()
        bad_people = []
        for mentor in mentors:
            if mentor[0] in blank:
                bad_people.append(mentor[0])
            else:
                blank.add(mentor[0])
        raise ValueError("There were at least two mentors with the exact same name. Check {}".format(bad_people))

    # Verify that each mentor selected a list of valid candidates
    for preference_list in mentors:
        mentor_name = preference_list[0]
        if check_year:
            year = mentors_years[mentor_name]
        for cand in preference_list[1:]:
            if cand not in candidate_names:
                if verbose:
                    print("Warning: Mentor {} specified a candidate who doesn't exist ({})".format(mentor_name, cand))
                preference_list.remove(cand)
            # Short circuit the dictionary lookup
            elif check_year and candidates_years[cand] <= year:
                if verbose:
                    print("Warning: Mentor {} (year {}) requested a candidate who is too old ({}, year {})"
                        .format(mentor_name, year, cand, candidates_years[cand]))
                preference_list.remove(cand)

    # Verify that each candidate selected a list of valid mentors
    for preference_list in candidates:
        cand_name = preference_list[0]
        if check_year:
            year = candidates_years[cand_name]
        for mentor in preference_list[1:]:
            if mentor not in mentor_names:
                if verbose:
                    print("Warning: Candidate {} specified a mentor who doesn't exist ({})".format(cand_name, mentor))
                preference_list.remove(mentor)
            elif check_year and mentors_years[mentor] >= year:
                if verbose:
                    print("Warning: Candidate {} (year {}) requested a mentor who is too young ({}, year {})"
                        .format(cand_name, year, mentor, mentors_years[mentor]))

def read_and_preprocess(mentor_file, candidate_file, n):
    """
    Reads and formats the mentor and candidate data from a raw CSV

    Parameters
    --------------------
    mentor_file: File location of the mentor csv
    candidate_file: File location of the candidate csv
    n: Number of preferences to read

    Returns
    --------------------
    Tuple containing: 
    0. List of the preference list of all mentors (mentor name is element 0 of each row)
    1. List of the preference list of all candidates (candidate name is element 0 of each row)
    2. Dictionary mapping from mentor name to mentor year
    3. Dictionary mapping from candidate name to candidate year
    """
    candidates = read_dataframe_candidate(candidate_file, n).values.tolist()
    mentors = read_dataframe_mentor(mentor_file, n).values.tolist()

    # Convert everything to lower and strip whitespace per entry
    # Exclude year (the last row) while converting things
    # This should probably be done in pandas, but I am not good with pandas
    for i in range(len(candidates)):
        for j in range(len(candidates[i]) - 1):
            candidates[i][j] = candidates[i][j].lower().strip()
    for i in range(len(mentors)):
        for j in range(len(mentors[i]) - 1):
            mentors[i][j] = mentors[i][j].lower().strip()

    # Create dictionaries that map from the member's name to the member's year
    candidates_years = {}
    for candidate_row in candidates:
        candidates_years[candidate_row[0]] = candidate_row[len(candidate_row) - 1]
    mentors_years = {}
    for mentor_row in mentors:
        mentors_years[mentor_row[0]] = mentor_row[len(mentor_row) - 1]

    # Remove the years column now
    candidates = [row[:-1] for row in candidates]
    mentors = [row[:-1] for row in mentors] 

    # Ensure that no one specified a member who doesn't exist or is in an invalid year
    validate_data(mentors, candidates, mentors_years, candidates_years, verbose = True)

    return mentors, candidates, mentors_years, candidates_years

################################################################################
### Utility
################################################################################
def fill_list(preference_list, name_set):
    """
    Returns a full preference list, appending names from name_set that aren't in preference_list to the back.
    Unspecified names are put in alphabetical order.

    Parameters
    --------------------
    preference_list: Incomplete partial list of names that represent a preference order
    name_set: Set of all possible names that could have been chosen for a preference

    Returns
    --------------------
    Full list of preferences that preserves the initial ordering of preference_list and contains all other names.
    """
    l = [preference_list[0]]
    names = name_set.copy()
    for name in preference_list[1:]:
        # Remove duplicates as well
        if name not in l:
            l.append(name)
        # This check is needed so people who put the same person twice don't throw an error
        if name in names:
            names.remove(name)
    l.extend(sorted(list(names)))
    return l

def fill_with_valid(mentors, candidates, mentors_years, candidates_years):
    """
    Returns a full preference list for all mentors and candidates, filled with all year-valid candidates/mentors

    Parameters
    --------------------
    mentors: List of the preference list of all mentors (mentor name is element 0 of each row)
    candidates: List of the preference list of all candidates (candidate name is element 0 of each row)
    mentors_years: Dictionary mapping from mentor name to mentor year
    candidates_years: Dictionary mapping from candidate name to candidate year

    Returns
    --------------------
    Tuple containing: 
    0. Full preference list for all mentors (mentor name is element 0 of each row)
    1. Full preference list for all candidates (candidate name is element 0 of each row)
    """
    candidates_filled = [fill_list(c, set([m[0] for m in mentors if mentors_years[m[0]] < candidates_years[c[0]]])) for c in candidates]
    mentors_filled = [fill_list(m, set([c[0] for c in candidates if candidates_years[c[0]] > mentors_years[m[0]]])) for m in mentors]

    return mentors_filled, candidates_filled

################################################################################
### Matching Helpers
################################################################################
def match_top_choices(mentors, candidates):
    """
    Produces matches (M, C) between mentors and candidates that satisfy the following criteria: 
    1. Mentor M has candidate C as their top choice
    2. Candidate C has mentor M as their top choice

    Parameters
    --------------------
    mentors: List of the preference list of all mentors (mentor name is element 0 of each row)
    candidates: List of the preference list of all candidates (candidate name is element 0 of each row)

    Returns
    --------------------
    List of pairings as described above
    """
    successful_pairings = []
    # Lookup if their number one candidate also has them as their #1
    for mentor, preference_list in mentors.items():
        # if they put all their people as people that don't exist lmao
        if len(preference_list) == 0:
            continue
        # its a match
        if candidates[preference_list[0]][0] == mentor:
            successful_pairings.append((mentor, preference_list[0]))

    return successful_pairings

def match_no_preference(group1, group2, max_to_scan = 5):
    """
    Produces matches (G1, G2) between group1 and group2 that satisfy the following criteria:
    1. G1 has no member of group2 in their preference list
    2. G2 has member G1 in their top max_to_scan

    Priority over no-preference group1 members is given to group2 members that have them as higher preference.
    For instance, if G1 has no member of group2 in their top 5, and G has G1 as their top 2 but G' has G1 as their top,
        then G1 is matched with G' instead of G.

    Parameters
    --------------------
    group1: List of the preference list of all group1 members (name is element 0 of each row)
    group2: List of the preference list of all group2 members (name is element 0 of each row)
    max_to_scan: Integer describing how far down the preference lists to look for matching members

    Returns
    --------------------
    List of pairings as described above
    """
    # Determine which members of group1 have no members of group2 in preference list
    # Index 0 is the member name, Index 1+ is the preference list
    no_preference_members = []
    for preference_list in group1:
        if len(preference_list[1:]) == 0:
            no_preference_members.append(preference_list[0])

    # Determine if any members of group2 want these no preference members
    # First scan if any group2 members have them as first, then second, etc.
    no_preference_pairings = []
    for i in range(1, max_to_scan):
        # List of preference i pairings, (group2, group1)
        # This can be one-lined
        preference_i_pairings = []
        for row in group2:
            # member name is index 0, preference i is index i
            if len(row) > i:
                preference_i_pairings.append((row[0], row[i]))
        for pairing in preference_i_pairings:
            if pairing[1] in no_preference_members:
                no_preference_pairings.append([pairing[1], pairing[0]])
                # pairing[1] is now matched, remove from the list of no preference
                no_preference_members.remove(pairing[1])

    return no_preference_pairings

################################################################################
### Main
################################################################################
def main():
    """
    Main function for stable_marriage_csv.py.
    This script takes in two required arguments: A mentor CSV file and a candidate CSV file.
    Each CSV file must contain at least the member's name, year, and preference list of the other group.
    The script attempts to perform stable matching between these two groups based on the preference lists.
    The resulting matches are written to an output CSV, containing the mentor, candidate, and how they were matched.
    If stable matching is not possible (for instance, due to restrictions from the year), then no pairings are written.
    """
    args = parse_arguments()

    ##### READ AND PREPROCESS DATA #####
    mentors, candidates, mentors_years, candidates_years = read_and_preprocess(args.mentor_file, args.candidate_file, args.num_preferences)

    # Store a copy of the initially declared preferences (after filtering)
    # This is used later to see how many people didn't get someone in their top 
    candidate_dict_initial = list_to_dictionary(candidates)
    mentor_dict_initial = list_to_dictionary(mentors)

    ##### PAIR BASED ON FIRST CHOICES #####
    successful_pairings = match_top_choices(list_to_dictionary(mentors), list_to_dictionary(candidates))
    print("Paired {} people based on first choices".format(len(successful_pairings)))
    remove_pairings(successful_pairings, mentors, candidates)

    ##### PAIR BASED ON ONE-SIDED PREFERENCE #####
    ## ONE SIDED CANDIDATES
    one_sided_candidate_pairings = match_no_preference(candidates, mentors)
    print("Paired {} people based on candidates with no mentor preferences".format(len(one_sided_candidate_pairings)))
    remove_pairings(one_sided_candidate_pairings, candidates, mentors)

    ## ONE SIDED MENTORS
    one_sided_mentor_pairings = match_no_preference(mentors, candidates)
    print("Paired {} people based on mentors with no candidate preferences".format(len(one_sided_mentor_pairings)))
    remove_pairings(one_sided_mentor_pairings, mentors, candidates)

    # Fill the remaining preference list with the valid unspecified mentors/candidates
    mentors_filled, candidates_filled = fill_with_valid(mentors, candidates, mentors_years, candidates_years)

    candidate_dict = list_to_dictionary(candidates_filled)
    mentor_dict = list_to_dictionary(mentors_filled)

    stable_matches = stable_matching.stable_marriage(mentor_dict, candidate_dict)
    stable_match_success = (len(stable_matches) != 0)
    if stable_match_success:
        print("Paired {} people based on stable matching".format(len(stable_matches)))
    else:
        print("Warning: Could not determine a stable match with the optimizations.")
        print("Attempting to stable match without...")
        mentors, candidates, mentors_years, candidates_years = read_and_preprocess(args.mentor_file, args.candidate_file, args.num_preferences)
        # Fill the remaining preference list with the valid unspecified mentors/candidates
        mentors_filled, candidates_filled = fill_with_valid(mentors, candidates, mentors_years, candidates_years)

        candidate_dict = list_to_dictionary(candidates_filled)
        mentor_dict = list_to_dictionary(mentors_filled)

        # Stable match immediately
        stable_matches = stable_matching.stable_marriage(mentor_dict, candidate_dict)
        if len(stable_matches) == 0:
            print("Error: Could not stable match these preference lists.")
            return

    # Combine the pairings from all sources into a single list
    if stable_match_success:
        all_pairings = []
        for mentor, candidate in successful_pairings:
            all_pairings.append([mentor, candidate, "Paired based on first choice"])
        for mentor, candidate in one_sided_mentor_pairings:
            all_pairings.append([mentor, candidate, "Paired based on one-sided mentors"])
        for candidate, mentor in one_sided_candidate_pairings:
            all_pairings.append([mentor, candidate, "Paired based on one-sided candidates"])
        for mentor, candidate in stable_matches:
            mentor_name = mentor
            if mentor is None:
                mentor_name = "No mentor"
            candidate_name = candidate
            if candidate is None:
                candidate_name = "No candidate"
            all_pairings.append([mentor_name, candidate_name, "Paired based on stable matching"])
    else:
        all_pairings = stable_matches

    output_file = "pairings.csv"
    if args.output_file:
        output_file = args.output_file
    with open(output_file, "w+") as f:
        f.write("Mentor,Candidate,Notes\n")
        for mentor, candidate, notes in all_pairings:
            f.write("{},{},{}\n".format(mentor, candidate, notes))

if __name__ == '__main__':
    main()
