#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 servername"
    echo "test that jobs can be listed  on server"
    exit 0
fi
source ./setup_env.sh

JOB=$1

$EXEPATH/jobsub_q.py --group $GROUP $SERVER_SPEC --debug
T1=$?
$EXEPATH/jobsub_q.py --group $GROUP $SERVER_SPEC --jobid $JOB
T2=$?
$EXEPATH/jobsub_q.py $SERVER_SPEC --summary 
T3=$?

! (( $T1 || $T2 || $T3 ))
T4=$?
echo $0 exiting with status $T4
exit $T4

