#!/bin/sh
GROUP=`id -gn`
if [ "$1" = "" ]; then
    echo "usage: $0 servername"
    echo "test that jobsub help is implemented on server"
    exit 0
fi
MACH=$1
curl -k  --cert /tmp/x509up_u${UID}  -H "Accept: text/html" -X GET https://${MACH}:8443/jobsub/acctgroups/$GROUP
