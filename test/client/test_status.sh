#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 servername"
    echo "test that jobsub help is implemented on server"
    exit 0
fi
source ./setup_env.sh

$EXEPATH/jobsub_status $GROUP_SPEC $SERVER_SPEC --sites 
T1=$?
TFINAL=$T1
echo $0 exiting with status $TFINAL
exit $TFINAL

