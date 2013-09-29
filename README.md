```
#! /bin/sh
# /etc/init.d/sprinkler 

### BEGIN INIT INFO
# Provides:          sprinkler
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Simple script to start a program at boot
# Description:       Run script at startup
### END INIT INFO

# If you want a command to always run, put it here

# Carry out specific functions when asked to by the system
case "$1" in
  start)
    echo "Starting sprinkler"
    # run application you want to start
    /home/pi/sprinkler/auto.py &
    ;;
  stop)
    echo "Stopping sprinkler"
    # kill application you want to stop
    killall auto.py
    ;;
  *)
    echo "Usage: /etc/init.d/sprinkler {start|stop}"
    exit 1
    ;;
esac

exit 0
```

API
===
Base: `/sprinkler/api/v1.0/`

| HTTP Method |  URI (added to base)  | Action                        |
|:-----------:|-----------------------|-------------------------------|
|     GET     | programs/             | Retrieve all programs         |
|     GET     | programs/[program_id] | Retrieve a program            |
|     POST    | programs/             | Create a new program          |
|     PUT     | programs/[program_id] | Update an existing program    |
|    DELETE   | programs/[program_id] | Delete a program              |
|     POST    | programs/now/         | Run sprinkler set immediately |
|     GET     | programs/status/      | Get current status of zones   |