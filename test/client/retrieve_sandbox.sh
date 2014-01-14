#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 server [clusterid] "
    echo "retrieve job (clusterid)'s output back from server"
    exit 0
fi
MACH=$1
CLUSTER=$2
if [ "$CLUSTER" = "" ];then
    CLUSTER=1
fi
#hardcode group for now
GROUP=nova
curl -k --cert /tmp/x509up_u${UID} -H "Accept: application/x-download" -o $CLUSTER.zip -X GET https://${MACH}:8443/jobsub/acctgroups/${GROUP}/jobs/${CLUSTER}/sandbox/
