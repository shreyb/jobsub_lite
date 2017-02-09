#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 server [joblist] "
    echo " hold and relieve list of jobs on server"
    exit 0
fi
source ./setup_env.sh
JOBLIST=`echo "$@"|sed 's/\s\+/,/g'`

export SERVER=https://${MACH}:8443
echo before
$EXEPATH/jobsub_q.py $GROUP_SPEC $SERVER_SPEC   $OTHER_TEST_FLAGS
T1=$?
echo test removing joblist=${JOBLIST}
$EXEPATH/jobsub_rm.py $GROUP_SPEC $SERVER_SPEC  --jobid $JOBLIST --debug $OTHER_TEST_FLAGS
T2=$?
echo after 
$EXEPATH/jobsub_q.py $GROUP_SPEC $SERVER_SPEC   $OTHER_TEST_FLAGS
T3=$?


! (( $T1 || $T2 || $T3 ))
TFINAL=$?
echo $0 exiting with status $TFINAL
exit $TFINAL

