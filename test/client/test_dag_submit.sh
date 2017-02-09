#!/bin/sh

source ./setup_env.sh

export SERVER=https://${MACH}:8443

cd jobsubDagTest
$EXEPATH/jobsub_submit_dag $SUBMIT_FLAGS  $GROUP_SPEC \
--debug $SERVER_SPEC  file://dagTest  --maxConcurrent 3
T1=$?
echo T1=$T1
$EXEPATH/jobsub_submit_dag $SUBMIT_FLAGS  $GROUP_SPEC \
--debug $SERVER_SPEC  file://dagTest2  
T2=$?
echo T2=$T2
$EXEPATH/jobsub_submit_dag $SUBMIT_FLAGS  $GROUP_SPEC \
--debug $SERVER_SPEC  file://dagTest3  
T3=$?
echo T3=$T3
$EXEPATH/jobsub_submit_dag $SUBMIT_FLAGS  $GROUP_SPEC \
--debug $SERVER_SPEC  file://dagTest4  
T4=$?
echo T4=$T4
$EXEPATH/jobsub_submit_dag $SUBMIT_FLAGS  $GROUP_SPEC \
--debug $SERVER_SPEC  file://dagTest5  
T5=$?
echo T5=$T5
cd -
! (( $T1 || $T2 || $T3  || $T4 || $T5 ))
TFINAL=$?
echo $0 exiting with status $TFINAL
exit $TFINAL

