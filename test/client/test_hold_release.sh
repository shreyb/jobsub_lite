#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 server [joblist] "
    echo " hold and relieve list of jobs on server"
    exit 0
fi
source ./setup_env.sh
JOBLIST=`echo "$@"|sed 's/\s\+/,/g'`

echo before
condor_q -name $MACH -pool $POOL
$EXEPATH/jobsub_hold.py --group $GROUP $SERVER_SPEC  --jobid $JOBLIST
echo after hold
condor_q -name $MACH -pool $POOL
$EXEPATH/jobsub_release.py --group $GROUP $SERVER_SPEC  --jobid $JOBLIST
echo after release
condor_q -name $MACH -pool $POOL

