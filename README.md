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

* Oracle VirtualBox
* 2 VM set up with the latest ubuntu LTE.
* both VM on the same network
* passwordless sudo set on both vm
* ansible installed on controller vm

### Installing

Controller VM:
- Create a user named 'rem' (all lower case)
- set network ip to 10.0.2.15
- download configure.yml, deploy.yml, and inventory.ini and put them in your desired folder
- run this in cmd for passwordless sudo
  ```
  echo "ansible_user ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/ansible
  sudo chmod 440 /etc/sudoers.d/ansible
  ```
Host VM:
- Create a user named 'momo' (all lower case)
- set network ip to 10.0.2.5
- run this in cmd for passwordless sudo
  ```
  echo "ansible_user ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/ansible
  sudo chmod 440 /etc/sudoers.d/ansible
  ```

### Executing program

1. download configure.yml, deploy.yml, and inventory.ini into a folder of your choosing. Make sure they are in the same folder
2. run 
```
ansible-playbook -i inventory.ini configure.yml
ansible-playbook -i inventory.ini deploy.yml
```

## NOTES:

- the inital users and ip doesn't matter but the passwordless sudos are a must
- sometimes ansible can't reach host when I am not actively log into the 2nd vm even when it's powered on.




