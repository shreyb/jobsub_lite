#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 servername"
    echo "test that jobs can be listed  on server"
    exit 0
fi
source ./setup_env.sh


JOB=$1

$EXEPATH/jobsub_q.py --debug $GROUP_SPEC $SERVER_SPEC --long
T1=$?
$EXEPATH/jobsub_q.py --debug $GROUP_SPEC $SERVER_SPEC --jobid $JOB --long
T2=$?
$EXEPATH/jobsub_q.py --debug $GROUP_SPEC $SERVER_SPEC --jobid $JOB --user $USER --long
T3=$?
#don't do this test on production server it takes forever and fills up the disk
T4=0
if [ "$SERVER_SPEC" != "https://fifebatch.fnal.gov:8443" ]; then
    $EXEPATH/jobsub_q.py --debug $SERVER_SPEC --long
    T4=$?
fi
$EXEPATH/jobsub_q.py --debug $SERVER_SPEC --user $USER --long
T5=$?
$EXEPATH/jobsub_q.py --debug $SERVER_SPEC --jobid $JOB --long
T6=$?
$EXEPATH/jobsub_q.py --debug $SERVER_SPEC --user $USER --jobid $JOB --long
T7=$?
$EXEPATH/jobsub_q.py --debug $GROUP_SPEC $SERVER_SPEC  --user $USER --long
T8=$?

! (( $T1 || $T2 || $T3 || $T4 || $T5 || $T6 || $T7 || $T8 ))
TT=$?
echo $0 exiting with status $TT
exit $TT

