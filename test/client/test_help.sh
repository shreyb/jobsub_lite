#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 servername"
    echo "test that jobsub help is implemented on server"
    exit 0
fi
source ./setup_env.sh

#curl -k  --cert /tmp/x509up_u${UID}  -H "Accept: text/html" -X GET https://${MACH}:8443/jobsub/acctgroups/${GROUP}/help/

$EXEPATH/jobsub_submit.py $SERVER_SPEC --help
T1=$?
$EXEPATH/jobsub_submit.py \
  $SERVER_SPEC \
  --group $GROUP --help
T2=$?

! (( $T1 || $T2 ))
T3=$?
echo $0 exiting with status $T3
exit $T3

