#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 servername"
    echo "test that jobs can be listed  on server"
    exit 0
fi
source ./setup_env.sh


JOB=$1

$EXEPATH/jobsub_q.py  --debug $GROUP_SPEC $SERVER_SPEC 
T1=$?
$EXEPATH/jobsub_q.py  --debug $GROUP_SPEC $SERVER_SPEC --jobid $JOB
T2=$?
$EXEPATH/jobsub_q.py  --debug $GROUP_SPEC $SERVER_SPEC --jobid $JOB --user $USER 
T3=$?
$EXEPATH/jobsub_q.py  --debug $SERVER_SPEC 
T4=$?
$EXEPATH/jobsub_q.py  --debug $SERVER_SPEC --user $USER
T5=$?
$EXEPATH/jobsub_q.py  --debug $SERVER_SPEC --jobid $JOB
T6=$?
$EXEPATH/jobsub_q.py  --debug $SERVER_SPEC --user $USER --jobid $JOB
T7=$?
$EXEPATH/jobsub_q.py  --debug $SERVER_SPEC --summary 
T8=$?
$EXEPATH/jobsub_q.py  --debug $GROUP_SPEC $SERVER_SPEC  --user $USER 
T9=$?

! (( $T1 || $T2 || $T3 || $T4 || $T5 || $T6 || $T7 || $T8 || $T9 ))
TT=$?
echo $0 exiting with status $TT
exit $TT

