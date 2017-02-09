#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 servername"
    echo "test that jobs can be listed  on server"
    exit 0
fi
source ./setup_env.sh

JOB=$1
T1=0
echo $SERVER_SPEC | grep fifebatch.fnal.gov:8443 > /dev/null 2>&1
if [ "$?" != "0" ]; then
    $EXEPATH/jobsub_history  $GROUP_SPEC $SERVER_SPEC
    T1=$?
fi
echo T1=$T1
$EXEPATH/jobsub_history  $GROUP_SPEC $SERVER_SPEC --jobid $JOB
T2=$?
echo T2=$T2
$EXEPATH/jobsub_history  $GROUP_SPEC $SERVER_SPEC --user $USER
T3=$?
echo T3=$T3
$EXEPATH/jobsub_history  $GROUP_SPEC $SERVER_SPEC --user $USER --jobid $JOB
T4=$?
echo T4=$T4


! (( $T1 || $T2 || $T3 || $T4 ))
TFINAL=$?
echo $0 exiting with status $TFINAL
exit $TFINAL

