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
CLUSTER=$1
if [ "$CLUSTER" = "" ];then
    CLUSTER=1
fi
export SERVER=https://${MACH}:8443
mkdir -p jobsubjobsection/${GROUP}
if [ "$JOBSUB_GROUP" != "" ]; then
    GROUP=$JOBSUB_GROUP
fi
if [ "$3" != "" ]; then
    ROLE=" --role $3 "
fi
OUTDIR=jobsubjobsection/${GROUP}/$CLUSTER
try $EXEPATH/jobsub_fetchlog.py $ROLE $OTHER_TEST_FLAGS --group $GROUP --jobsub-server $SERVER --jobid $CLUSTER --dest-dir $OUTDIR 
N1=`ls $OUTDIR/*.cmd | wc -l`
N2=`grep JOBSUBJOBSECTION $OUTDIR/*.cmd | wc -l`
N3=`grep JobsubJobSection $OUTDIR/*.cmd | wc -l`
echo "for DAG job $CLUSTER , $N1 command files were generated,  $N2  contain JOBSUBJOBSECTION and $N3 contain JobsubJobSection"
try test $N1 = $N2 -a $N2 = $N3
