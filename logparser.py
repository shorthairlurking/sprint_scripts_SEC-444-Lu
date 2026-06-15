
#SEC444 sprint 1 logparser.py
#Licensed under the MIT License (https://opensource.org/license/mit)
#Version: Ski-20260615

#Initial variables and imports

import re
import csv
import sys


#Script | Library | Functions

## Regex to capture Timestamp, Host, PID, User, IP, and Port
# Pattern: Apr 14 00:28:06 linux1 sshd[1006]: Failed password for admin from 142.146.24.37 port 16271 ssh2
LOG1 = r"(?P<date>\w+\s+\d+\s\d+:\d+:\d+)\s(?P<host>\S+)\ssshd\[(?P<pid>\d+)\]:\sFailed\spassword\sfor\s(?P<user>\w+)\sfrom\s(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\sport\s(?P<port>\d+)\sssh2"

# Pattern: Apr 14 00:28:14 linux1 sshd[1009]: Failed password for invalid user test from 142.146.24.37 port 23322 ssh2
LOG2 = r"(?P<date>\w+\s+\d+\s\d+:\d+:\d+)\s(?P<host>\S+)\ssshd\[(?P<pid>\d+)\]:\sFailed\spassword\sfor\sinvalid\suser\s(?P<user>\w+)\sfrom\s(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\sport\s(?P<port>\d+)\sssh2"

# Pattern: Apr 14 02:08:57 linux1 sshd[1085]: Failed password for invalid user ec2-user from 192.241.218.198 port 7576 ssh2
LOG3 = r"(?P<date>\w+\s+\d+\s\d+:\d+:\d+)\s(?P<host>\S+)\ssshd\[(?P<pid>\d+)\]:\sFailed\spassword\sfor\sinvalid\suser\s(?P<user>\w+\W\w+)\sfrom\s(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\sport\s(?P<port>\d+)\sssh2"

def parse_ssh_failures(target_list, output_csv):
    failed_attempts = []
    
    try:
        with open(target_list, "r") as f:
            for line in f:
                #match LOG3, LOG2, then LOG1
                match = re.search(LOG3, line)
                if match:
                    entry = match.groupdict()
                    failed_attempts.append(entry)
                    print(f"Timestamp: {entry['date']} Host: {entry['host']} |PID: {entry['pid']}| User: {entry['user']} | IP: {entry['ip']} | Port: {entry['port']}")
                else:
                    match = re.search(LOG2, line)
                    if match:
                        entry = match.groupdict()
                        failed_attempts.append(entry)
                        print(f"Timestamp: {entry['date']} Host: {entry['host']} |PID: {entry['pid']}| User: {entry['user']} | IP: {entry['ip']} | Port: {entry['port']}")
                    else:
                        match = re.search(LOG1, line)
                        if match:
                            entry = match.groupdict()
                            failed_attempts.append(entry)
                            print(f"Timestamp: {entry['date']} Host: {entry['host']} |PID: {entry['pid']}| User: {entry['user']} | IP: {entry['ip']} | Port: {entry['port']}")
    except PermissionError:
        print(f"Error: Access denied. Try running with 'sudo'.")
        return
    except FileNotFoundError:
        print(f"Error: Log file {target_list} not found.")
        return

    # Output to CSV
    with open(output_csv, "w", newline='') as csvfile:
        fieldnames = ['date', 'host', 'pid', 'user', 'ip', 'port']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(failed_attempts)
    
    print(f"\nSuccessfully saved {len(failed_attempts)} attempts to {output_csv}")

def main():
    if len(sys.argv) != 3:
        print("Usage: python logparser.py <target_list> <output_csv>")
        sys.exit(1)

    target_list = sys.argv[1]
    output_csv  = sys.argv[2]   

    parse_ssh_failures(target_list, output_csv)

if __name__ == "__main__":
    main()
