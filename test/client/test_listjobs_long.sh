#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 servername"
    echo "test that jobs can be listed  on server"
    exit 0
fi
source ./setup_env.sh


JOB=$1

$EXEPATH/jobsub_q.py --debug $GROUP_SPEC $SERVER_SPEC --long $OTHER_TEST_FLAGS
T1=$?
echo T1=$T1
$EXEPATH/jobsub_q.py --debug $GROUP_SPEC $SERVER_SPEC --jobid $JOB --long $OTHER_TEST_FLAGS
T2=$?
echo T2=$T2 
$EXEPATH/jobsub_q.py --debug $GROUP_SPEC $SERVER_SPEC --jobid $JOB --user $USER --long $OTHER_TEST_FLAGS
T3=$?
echo T3=$T3
#don't do this test on production server it takes forever and fills up the disk
T4=0
echo SERVER_SPEC=$SERVER_SPEC
echo $SERVER_SPEC | grep fifebatch.fnal.gov:8443 >/dev/null 2>&1
if [ "$?" != "0" ]; then
    $EXEPATH/jobsub_q.py --debug $SERVER_SPEC --long $OTHER_TEST_FLAGS
    T4=$?
fi
echo T4=$T4
$EXEPATH/jobsub_q.py --debug $SERVER_SPEC --user $USER --long $OTHER_TEST_FLAGS
T5=$?
echo T5=$T5
$EXEPATH/jobsub_q.py --debug $SERVER_SPEC --jobid $JOB --long $OTHER_TEST_FLAGS
T6=$?
echo T6=$T6
$EXEPATH/jobsub_q.py --debug $SERVER_SPEC --user $USER --jobid $JOB --long $OTHER_TEST_FLAGS
T7=$?
echo T7=$T7
$EXEPATH/jobsub_q.py --debug $GROUP_SPEC $SERVER_SPEC  --user $USER --long $OTHER_TEST_FLAGS
T8=$?
echo T8=$T8

! (( $T1 || $T2 || $T3 || $T4 || $T5 || $T6 || $T7 || $T8 ))
TT=$?
echo $0 exiting with status $TT
exit $TT

