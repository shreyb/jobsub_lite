#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 servername"
    echo "test that jobs can be listed  on server"
    exit 0
fi
source ./setup_env.sh


JOB=$1

$EXEPATH/jobsub_q.py $GROUP_SPEC $SERVER_SPEC --long
T1=$?
$EXEPATH/jobsub_q.py $GROUP_SPEC $SERVER_SPEC --jobid $JOB --long
T2=$?
$EXEPATH/jobsub_q.py $GROUP_SPEC $SERVER_SPEC --jobid $JOB --user $USER --long
T3=$?
$EXEPATH/jobsub_q.py $SERVER_SPEC --long
T4=$?
$EXEPATH/jobsub_q.py $SERVER_SPEC --user $USER --long
T5=$?
$EXEPATH/jobsub_q.py $SERVER_SPEC --jobid $JOB --long
T6=$?
$EXEPATH/jobsub_q.py $SERVER_SPEC --user $USER --jobid $JOB --long
T7=$?

! (( $T1 || $T2 || $T3 || $T4 || $T5 || $T6 || $T7 ))
TT=$?
echo $0 exiting with status $TT
exit $TT

