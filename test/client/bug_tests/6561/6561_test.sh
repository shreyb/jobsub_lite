#!/bin/sh

if [ "$1" = "" ]; then
    echo "usage $0 server script_to_submit [script args]"
    echo "test submission to jobsub client/server architecture"
    exit 0
fi
cd ../../
source ./setup_env.sh
cd -

export SERVER=https://${MACH}:8443

$EXEPATH/jobsub_submit.py --group $GROUP --debug \
       $SERVER_SPEC \
            -e SERVER --nowrapfile -l 'notify_email=foo@bar.com'  file://6561.sh foo@bar.com

$EXEPATH/jobsub_submit.py --group $GROUP \
       $SERVER_SPEC \
           -g -e SERVER  -l 'notify_email=foo@bar.com'  file://6561.sh foo@bar.com
