#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 servername"
    echo "test that jobs can be listed  on server"
    exit 0
fi
source ./setup_env.sh

JOB=$1

$EXEPATH/jobsub_history $GROUP_SPEC $SERVER_SPEC
T1=$?
$EXEPATH/jobsub_history $GROUP_SPEC $SERVER_SPEC --jobid $JOB
T2=$?
$EXEPATH/jobsub_history $GROUP_SPEC $SERVER_SPEC --user $USER
T3=$?
$EXEPATH/jobsub_history $GROUP_SPEC $SERVER_SPEC --user $USER --jobid $JOB
T4=$?


! (( $T1 || $T2 || $T3 || $T4 ))
TFINAL=$?
echo $0 exiting with status $TFINAL
exit $TFINAL

