#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 servername"
    echo "test that jobs can be listed  on server"
    exit 0
fi
source ./setup_env.sh


JOB=$1

$EXEPATH/jobsub_q  $OTHER_TEST_FLAGS  --debug $GROUP_SPEC $SERVER_SPEC 
T1=$?
echo T1=$T1
$EXEPATH/jobsub_q  --debug $GROUP_SPEC $SERVER_SPEC --jobid $JOB $OTHER_TEST_FLAGS 
T2=$?
echo T2=$T2
$EXEPATH/jobsub_q  --debug $GROUP_SPEC $SERVER_SPEC  $OTHER_TEST_FLAGS --jobid $JOB --user $USER 
T3=$?
echo T3=$T3
$EXEPATH/jobsub_q  --debug $SERVER_SPEC $OTHER_TEST_FLAGS  
T4=$?
echo T4=$T4
$EXEPATH/jobsub_q  --debug $SERVER_SPEC $OTHER_TEST_FLAGS  --user $USER
T5=$?
echo T5=$T5
$EXEPATH/jobsub_q   $OTHER_TEST_FLAGS --debug $SERVER_SPEC --jobid $JOB
T6=$?
echo T6=$T6
$EXEPATH/jobsub_q  --debug  $OTHER_TEST_FLAGS $SERVER_SPEC --user $USER --jobid $JOB
T7=$?
echo T7=$T7
$EXEPATH/jobsub_q  --debug $SERVER_SPEC --summary
T8=$?
echo T8=$T8
$EXEPATH/jobsub_q  --debug $GROUP_SPEC $SERVER_SPEC  --user $USER $OTHER_TEST_FLAGS  
T9=$?
echo T9=$T9

! (( $T1 || $T2 || $T3 || $T4 || $T5 || $T6 || $T7 || $T8 || $T9 ))
TFINAL=$?
echo $0 exiting with status $TFINAL
exit $TFINAL

