#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 servername"
    echo "test that jobs can be listed  on server"
    exit 0
fi
MACH=$1
source setup_env.sh

curl -k  --cert /tmp/x509up_u${UID}  -H "Accept: application/json" -X GET https://${MACH}:8443/jobsub/acctgroups/${GROUP}/jobs/
curl -k  --cert /tmp/x509up_u${UID}  -H "Accept: text/html" -X GET https://${MACH}:8443/jobsub/acctgroups/${GROUP}/jobs/
curl -k  --cert /tmp/x509up_u${UID}  -H "Accept: text/plain" -X GET https://${MACH}:8443/jobsub/acctgroups/${GROUP}/jobs/
