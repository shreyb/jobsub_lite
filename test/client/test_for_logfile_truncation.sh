#!/bin/sh
yell() { echo "$0: $*" >&2; }
die() { yell "$*"; exit 111; }
try() { echo "$@"; "$@" || die "FAILED $*"; }

if [ "$1" = "" ]; then
    echo "usage: $0 server [clusterid] "
    echo "retrieve job (clusterid)'s output back from server"
    exit 0
fi
source ./setup_env.sh
source ./noisy.env.sh

CLUSTER=$1
if [ "$CLUSTER" = "" ];then
    CLUSTER=1
fi
export SERVER=https://${MACH}:8443
#mkdir -p jobsubjobsection/${GROUP}
if [ "$JOBSUB_GROUP" != "" ]; then
    GROUP=$JOBSUB_GROUP
fi
if [ "$3" != "" ]; then
    ROLE=" --role $3 "
fi
OUTDIR=jobsubjobsection/${GROUP}/$CLUSTER
mkdir -p $OUTDIR
try $EXEPATH/jobsub_fetchlog.py  $OTHER_TEST_FLAGS $ROLE --group $GROUP --jobsub-server $SERVER --jobid $CLUSTER --dest-dir $OUTDIR 
TRUNCATED_FILE=`ls $OUTDIR/*.out`
P1="jobsub:---- truncated after $JOBSUB_MAX_JOBLOG_HEAD_SIZE bytes--"
P2="jobsub:---- resumed for last $JOBSUB_MAX_JOBLOG_TAIL_SIZE bytes--"
N1=`grep 'jobsub:---- truncated after' $TRUNCATED_FILE`
N2=`grep 'jobsub:---- resumed for last ' $TRUNCATED_FILE`
try test "$N1" = "$P1" -a "$N2" = "$P2"
