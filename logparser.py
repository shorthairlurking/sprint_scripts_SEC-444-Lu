
#SEC444 sprint 1 logparser.py
#Licensed under the MIT License (https://opensource.org/license/mit)
#Version: Ski-20260425

#Initial variables and imports

import re
import csv
import sys


#Script | Library | Functions

# Path to log file and output file
LOG_FILE ="/home/rem/SEC444/sample-auth.log" 
OUTPUT_CSV = "/home/rem/SEC444/failed_logins1.csv"

# Regex to capture Timestamp, Host, PID, User, IP, and Port
# Pattern: Apr 14 00:28:06 linux1 sshd[1006]: Failed password for admin from 142.146.24.37 port 16271 ssh2
LOG1 = "(?P<date>\w+\s+\d+\s\d+:\d+:\d+)\s(?P<host>\S+)\ssshd\[(?P<pid>\d+)\]:\sFailed\spassword\sfor\s(?P<user>\w+)\sfrom\s(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\sport\s(?P<port>\d+)\sssh2"
# Pattern: Apr 14 00:28:14 linux1 sshd[1009]: Failed password for invalid user test from 142.146.24.37 port 23322 ssh2
LOG2 = "(?P<date>\w+\s+\d+\s\d+:\d+:\d+)\s(?P<host>\S+)\ssshd\[(?P<pid>\d+)\]:\sFailed\spassword\sfor\sinvalid\suser\s(?P<user>\w+)\sfrom\s(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\sport\s(?P<port>\d+)\sssh2"
def parse_ssh_failures():
    failed_attempts = []
    
    try:
        with open(LOG_FILE, "r") as f:
            for line in f:
                #match with pattern 1 w/o invalid user
                match = re.search(LOG1, line)
                if match:
                    entry = match.groupdict()
                    failed_attempts.append(entry)
                    # Output to screen immediately
                    print(f"Timestamp: {entry['date']} Host: {entry['host']} |PID: {entry['pid']}| User: {entry['user']} | IP: {entry['ip']} | Port: {entry['port']}")
                #match with pattern 2 with invalid user
                match = re.search(LOG2, line)
                if match:
                    entry = match.groupdict()
                    failed_attempts.append(entry)
                    # Output to screen immediately
                    print(f"Timestamp: {entry['date']} Host: {entry['host']} |PID: {entry['pid']}| User: {entry['user']} | IP: {entry['ip']} | Port: {entry['port']}")
    except PermissionError:
        print(f"Error: Access denied. Try running with 'sudo'.")
        return
    except FileNotFoundError:
        print(f"Error: Log file {LOG_FILE} not found.")
        return

    # Output to CSV
    with open(OUTPUT_CSV, "w", newline='') as csvfile:
        fieldnames = ['date', 'host', 'pid', 'user', 'ip', 'port']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(failed_attempts)
    
    print(f"\nSuccessfully saved {len(failed_attempts)} attempts to {OUTPUT_CSV}")



#Run main() if script called directly

if __name__ == "__main__":
    parse_ssh_failures()
