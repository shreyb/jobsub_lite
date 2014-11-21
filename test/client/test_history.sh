#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 servername"
    echo "test that jobs can be listed  on server"
    exit 0
fi
source ./setup_env.sh

JOB=$1

$EXEPATH/jobsub_history.py $GROUP_SPEC $SERVER_SPEC
T1=$?
$EXEPATH/jobsub_history.py $GROUP_SPEC $SERVER_SPEC --jobid $JOB
T2=$?


! (( $T1 || $T2 ))
T3=$?
echo $0 exiting with status $T3
exit $T3

