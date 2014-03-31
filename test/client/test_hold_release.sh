#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 server [joblist] "
    echo " hold and relieve list of jobs on server"
    exit 0
fi
source ./setup_env.sh
MACH=$1
shift
JOBLIST=`echo "$@"|sed 's/\s\+/,/g'`

export SERVER=https://${MACH}:8443
GROUP=nova
echo before
condor_q -name $MACH -pool $MACH
$EXEPATH/jobsub_hold.py --group $GROUP --jobsub-server $SERVER  --jobid $JOBLIST
echo after hold
condor_q -name $MACH -pool $MACH
$EXEPATH/jobsub_release.py --group $GROUP --jobsub-server $SERVER  --jobid $JOBLIST
echo after release
condor_q -name $MACH -pool $MACH

