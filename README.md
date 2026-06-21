# ansible.py

A simple ansible playbook that setup and deploy servers.

## Description

For Sprint 5, the requirement for the scripts are:

- configure.yml configures your servers.
- deploy.yml deploys your Sprint 4 monitoring scripts to your servers.
- Use variables for anything that might change (paths, usernames, packages, etc.)
- Have descriptive names on every task
- Be idempotent. Running twice produces 0 changes on the second run

## Getting Started

### Dependencies

* 2 VM set up with the latest ubuntu LTE.
* both VM on the same network
* passwordless sudo set on both vm
* ansible installed on controller vm

### Installing

Controller VM:
- Create a user named 'rem' (all lower case)
    


### Executing program

1. download healthmon.py and config.json into a folder of your choosing. Make sure they are in the same folder
2. go to /home/ubuntu/ and paste healthmon.log and alerts.log in there. (they should be automatically created when you run the healthmon.py the first time but just in case)
3. open up command and navigate to the folder with healthmon.py.
4. run script by inputing the config.json --check 
   Example:
```
python3 healthmon.py config.json --check
```

