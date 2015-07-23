#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 server [joblist] "
    echo " hold and relieve list of jobs on server"
    exit 0
fi
source ./setup_env.sh
JOBLIST=`echo "$@"|sed 's/\s\+/,/g'`

echo before
$EXEPATH/jobsub_q --user $USER $GROUP_SPEC $SERVER_SPEC  
T1=$?
echo T1=$T1
echo holding $GROUP jobs belonging to $USER 
$EXEPATH/jobsub_hold $GROUP_SPEC $SERVER_SPEC  --user $USER --debug
T2=$?
echo T2=$T2
echo after hold
$EXEPATH/jobsub_q --user $USER $GROUP_SPEC $SERVER_SPEC  
T3=$?
echo T3=$T3
echo releasing $GROUP jobs belonging to $USER  
$EXEPATH/jobsub_release $GROUP_SPEC $SERVER_SPEC  --user $USER --debug
T4=$?
echo T4=$T4
echo after release
$EXEPATH/jobsub_q --user $USER $GROUP_SPEC $SERVER_SPEC  
T5=$?
echo T5=$T5
! (( $T1 || $T2 || $T3 || $T4 || $T5 ))
TFINAL=$?

echo $0 exiting with status $TFINAL
exit $TFINAL
