# netrecon.py

A simple logparser.

## Description

For Sprint 1, the requirement for the scripts are:

- Use python-nmap to scan a target for open ports
- Use the requests library to query a public API
- Combine data from multiple sources into one output

## Getting Started

### Dependencies

- Ubuntu 26.04 LTS
- Python 3
- sample-auth.log

### Installing

1. Download dependencies, logparser.py, and sample-auth.log. 

### Executing program

1. download logparser.py and sample-auth.log to a folder of your choosing
2. open up command and navigate to the folder with the logparser.py
3. run script by inputing the log you want to parse then an output.csv
   Example:
```
python logparser.py <target_list> <output_csv>
```
