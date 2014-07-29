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
$EXEPATH/jobsub_q.py --group $GROUP $SERVER_SPEC  
T1=$?
echo test removing joblist=${JOBLIST}
$EXEPATH/jobsub_rm.py --group $GROUP $SERVER_SPEC  --jobid $JOBLIST --debug
T2=$?
echo after 
$EXEPATH/jobsub_q.py --group $GROUP $SERVER_SPEC  
T3=$?


! (( $T1 || $T2 || $T3 ))
T4=$?
echo $0 exiting with status $T4
exit $T4

