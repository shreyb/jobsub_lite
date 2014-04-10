#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 servername"
    echo "test that jobsub help is implemented on server"
    exit 0
fi
source ./setup_env.sh
export MACH=$1
shift

export SERVER=https://${MACH}:8443

#curl -k  --cert /tmp/x509up_u${UID}  -H "Accept: text/html" -X GET https://${MACH}:8443/jobsub/acctgroups/${GROUP}/help/

$EXEPATH/jobsub_submit.py --help
$EXEPATH/jobsub_submit.py --jobsub-server=$SERVER --group $GROUP --help
