# Stable Marriage From CSV
Produce stable marriages between mentors and candidates, reading the preference lists from CSV files.
Resulting marriages are written to `pairings.csv`. 

This script is intended to be used as a guide only. 
Due to the the fact that I am lazy and did not test adequately, there may be scenarios in which it declares there is no stable matching but one actually exists.

## Usage
```
$ python3 stable_marriage_csv.py -h
usage: Utility script used to producing stable matches between mentors and candidates.
       [-h] [-o OUTPUT_FILE] [-n NUM_PREFERENCES] MENTOR_FILE CANDIDATE_FILE

positional arguments:
  MENTOR_FILE           CSV containing the preference lists submitted by the mentors
  CANDIDATE_FILE        CSV containing the preference lists submitted by the candidates

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_FILE, --output OUTPUT_FILE
                        location of the output file
  -n NUM_PREFERENCES    number of preferences for each to consider (default 5)
```

## Requirements
1. `python3`
2. `pandas`:
```
pip3 install pandas
```
