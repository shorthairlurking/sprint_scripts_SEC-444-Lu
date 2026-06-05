# healthmon.py

A simple health monitoring script that checks disk usage %, memory usage %, cup load in 1 min, sshd, and cron.

## Description

For Sprint 4, the requirement for the scripts are:

- Script takes a config file as an argument: healthmon.py <config.json>
- Add --check flag to display a summary report: healthmon.py <config.json> --check
- Config file defines thresholds and log file paths

  Example config.json used:
  
```
{
    "checks": {
        "disk_usage_percent": 80,
        "memory_usage_percent": 90,
        "cpu_load_1min": 2.0,
        "services": ["sshd", "cron"]
    },
    "log_file": "/home/ubuntu/healthmon.log",
    "alert_log": "/home/ubuntu/alerts.log"
}

```

## Getting Started

### Dependencies

* The amazon box we installed in class or a fresh install of linux with an internet connection
* argparse
* json
* logging
* logging.handlers
* os
* shutil
* subprocess
* sys
* from dataclasses import dataclass, field
* from datetime import datetime
* from pathlib import Path
* from typing import Optional
* python3

### Installing

* download the healthmon.py, config.json, healthmon.log, and alerts.log

### Executing program

1. download healthmon.py and config.json into a folder of your choosing. Make sure they are in the same folder
2. go to /home/ubuntu/ and paste healthmon.log and alerts.log in there. (they should be automatically created when you run the healthmon.py the first time but just in case)
3. open up command and navigate to the folder with healthmon.py.
4. run script by inputing the config.json --check 
   Example:
```
python3 healthmon.py config.json --check
```

