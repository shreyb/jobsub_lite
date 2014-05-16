#!/bin/sh

if [ "$1" = "" ]; then
    echo "usage $0 server script_to_submit [script args]"
    echo "test submission to jobsub client/server architecture"
    exit 0
fi
source ./setup_env.sh

export SERVER=https://${MACH}:8443

$EXEPATH/jobsub_submit.py --group $GROUP --debug \
       $SERVER_SPEC \
            -e SERVER --nowrapfile  file://"$@"

$EXEPATH/jobsub_submit.py --group $GROUP \
       $SERVER_SPEC \
           -g -e SERVER --nowrapfile  file://"$@"
