#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 server [joblist] "
    echo " change priority of [joblist] on \$server"
    exit 0
fi
source ./setup_env.sh
JOBLIST=`echo "$@"|sed 's/\s\+/ /g'`
T4=0

for JOB in $JOBLIST; do 
    $EXEPATH/jobsub_q $OTHER_TEST_FLAGS $GROUP_SPEC $SERVER_SPEC --jobid $JOB 
    T1=$?
    $EXEPATH/jobsub_prio  $OTHER_TEST_FLAGS $GROUP_SPEC $SERVER_SPEC --jobid $JOB --prio 314159 
    T2=$?
    $EXEPATH/jobsub_q $OTHER_TEST_FLAGS $GROUP_SPEC $SERVER_SPEC  --constraint "JobsubJobID=?=\"$JOB\" && JobPrio=?=314159"
    T3=$?
    ! (( $T1 || $T2 || $T3 || $T4 ))
    T4=$?
done
TFINAL=$T4

echo $0 exiting with status $TFINAL
exit $TFINAL
