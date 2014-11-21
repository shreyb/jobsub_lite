#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 servername"
    echo "test that jobs can be listed  on server"
    exit 0
fi
source ./setup_env.sh


JOB=$1

$EXEPATH/jobsub_q.py $GROUP_SPEC $SERVER_SPEC --debug
T1=$?
$EXEPATH/jobsub_q.py $GROUP_SPEC $SERVER_SPEC --jobid $JOB
T2=$?
$EXEPATH/jobsub_q.py $SERVER_SPEC --summary 
T3=$?
$EXEPATH/jobsub_q.py $SERVER_SPEC --user $USER 
T4=$?
$EXEPATH/jobsub_q.py $SERVER_SPEC 
T5=$?
$EXEPATH/jobsub_q.py $SERVER_SPEC --jobid $JOB
T6=$?
$EXEPATH/jobsub_q.py $SERVER_SPEC --user $USER --jobid $JOB
T7=$?

! (( $T1 || $T2 || $T3 || $T4 || $T5 || $T6 || $T7 ))
T5=$?
echo $0 exiting with status $T5
exit $T5

