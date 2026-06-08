# sysinfo.py

A simply code to collect system information from a Linux machine.

## Description

For Sprint 2, the requirement for the scripts are:

- The script collects system information from the local machine including hostname, OS info, CPU, memory, disk, IP address, MAC address, and uptime.
- The command line argument determines the output format. 'screen' displays the results to the terminal. 'csv' writes the results to sysinfo.csv. 'json' writes the results to sysinfo.json.

## Getting Started

### Dependencies

* The amazon box we installed in class or a fresh install of linux with an internet connection
* sys
* os
* csv
* json
* socket
* struct
* fcntl
* platform
* subprocess
* datetime import timedelta
* python3

### Installing

* download the sysinfo.py onto target machine.

### Executing program

1. download the sysinfo.py into the target machine and into a folder of your choosing.
2. navigate to the folder
4. In the command line, run sysinfo.py with either screen | csv | json to pick how you want the output to show as.
   To print to screen:
```
python3 sysinfo.py screen
```
To output to a sysinfo.csv file:
```
python3 sysinfo.py csv
```
To output into a sysinfo.json file:
```
python3 sysinfo.py json
```
