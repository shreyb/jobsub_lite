#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 server [joblist] "
    echo " hold and relieve list of jobs on server"
    exit 0
fi
source ./setup_env.sh
JOBLIST=`echo "$@"|sed 's/\s\+/,/g'`

echo before
$EXEPATH/jobsub_q.py --group $GROUP $SERVER_SPEC  
echo holding joblist=${JOBLIST}
$EXEPATH/jobsub_hold.py --group $GROUP $SERVER_SPEC  --jobid $JOBLIST --debug
echo after hold
$EXEPATH/jobsub_q.py --group $GROUP $SERVER_SPEC  
echo releasing joblist=${JOBLIST}
$EXEPATH/jobsub_release.py --group $GROUP $SERVER_SPEC  --jobid $JOBLIST --debug
echo after release
$EXEPATH/jobsub_q.py --group $GROUP $SERVER_SPEC  

