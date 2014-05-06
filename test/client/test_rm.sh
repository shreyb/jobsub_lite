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
condor_q -name $MACH -pool $POOL
$EXEPATH/jobsub_rm.py --group $GROUP $SERVER_SPEC  --jobid $JOBLIST
echo after 
condor_q -name $MACH -pool $POOL

