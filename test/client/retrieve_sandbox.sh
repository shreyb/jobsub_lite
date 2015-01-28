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
mkdir -p curl
mkdir -p python
mkdir -p unarchive
if [ "$JOBSUB_GROUP" != "" ]; then
    GROUP=$JOBSUB_GROUP
fi
cd curl
pwd
try curl -k --cert /tmp/x509up_u${UID} -H "Accept: application/x-download" -o $CLUSTER.zip -X GET $SERVER/jobsub/acctgroups/${GROUP}/jobs/${CLUSTER}/sandbox/
cd -
for FMT in "zip" "tar"; do
  for JOBSPEC in "--job" "--jobid" "-J"; do
    cd python
    pwd
        try $EXEPATH/jobsub_fetchlog.py $GROUP_SPEC --jobsub-server $SERVER --archive-format $FMT  $JOBSPEC $CLUSTER 
    cd ../unarchive
    pwd
    for ARCHIVESPEC in "--unzipdir" "--destdir" "--dest-dir"; do 
        UNZIPDIR=`echo $JOBSPEC|sed 's/-//g'`"$FMT-$ARCHIVESPEC"
        try $EXEPATH/jobsub_fetchlog.py --group $GROUP --jobsub-server $SERVER $JOBSPEC $CLUSTER $ARCHIVESPEC $UNZIPDIR 
    done
    cd -
  done
done
exit 0
