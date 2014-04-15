#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 servername"
    echo "test that jobs can be listed  on server"
    exit 0
fi
MACH=$1
source ./setup_env.sh
export SERVER=https://${MACH}:8443


$EXEPATH/jobsub_history.py --group $GROUP --jobsub-server $SERVER
