#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 server [joblist] "
    echo " hold and relieve list of jobs on server"
    exit 0
fi
source ./setup_env.sh
JOBLIST=`echo "$@"|sed 's/\s\+/,/g'`

echo before
$EXEPATH/jobsub_q $OTHER_TEST_FLAGS $GROUP_SPEC $SERVER_SPEC  
T1=$?
echo holding joblist=${JOBLIST}
$EXEPATH/jobsub_hold $OTHER_TEST_FLAGS $GROUP_SPEC $SERVER_SPEC  --jobid $JOBLIST --debug
T2=$?
echo after hold
$EXEPATH/jobsub_q $OTHER_TEST_FLAGS $GROUP_SPEC $SERVER_SPEC  
T3=$?
echo releasing joblist=${JOBLIST}
$EXEPATH/jobsub_release $OTHER_TEST_FLAGS $GROUP_SPEC $SERVER_SPEC  --jobid $JOBLIST --debug
T4=$?
echo after release
$EXEPATH/jobsub_q $OTHER_TEST_FLAGS $GROUP_SPEC $SERVER_SPEC  
T5=$?
echo holding joblist=${JOBLIST}
$EXEPATH/jobsub_hold $OTHER_TEST_FLAGS $GROUP_SPEC $SERVER_SPEC  --jobid $JOBLIST --debug
T6=$?
! (( $T1 || $T2 || $T3 || $T4 || $T5 || $T6 ))
TFINAL=$?

echo $0 exiting with status $TFINAL
exit $TFINAL
