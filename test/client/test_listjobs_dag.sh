#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 servername"
    echo "test that jobs can be listed  on server"
    exit 0
fi
source ./setup_env.sh


JOB=$1

$EXEPATH/jobsub_q.py --debug  $GROUP_SPEC $SERVER_SPEC --dag
T1=$?
$EXEPATH/jobsub_q.py --debug  $GROUP_SPEC $SERVER_SPEC --jobid $JOB --dag
T2=$?
$EXEPATH/jobsub_q.py --debug  $GROUP_SPEC $SERVER_SPEC --jobid $JOB --user $USER --dag
T3=$?
$EXEPATH/jobsub_q.py --debug  $SERVER_SPEC --dag
T4=$?
$EXEPATH/jobsub_q.py --debug  $SERVER_SPEC --user $USER --dag
T5=$?
$EXEPATH/jobsub_q.py --debug  $SERVER_SPEC --jobid $JOB --dag
T6=$?
$EXEPATH/jobsub_q.py --debug  $SERVER_SPEC --user $USER --jobid $JOB --dag
T7=$?
$EXEPATH/jobsub_q.py --debug  $GROUP_SPEC $SERVER_SPEC  --user $USER --dag
T8=$?

! (( $T1 || $T2 || $T3 || $T4 || $T5 || $T6 || $T7 || $T8 ))
TT=$?
echo $0 exiting with status $TT
exit $TT

