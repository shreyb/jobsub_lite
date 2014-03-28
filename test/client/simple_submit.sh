#!/bin/sh

if [ "$1" = "" ]; then
    echo "usage $0 server script_to_submit [script args]"
    echo "test submission to jobsub client/server architecture"
    exit 0
fi
source ./setup_env.sh
export MACH=$1
shift

export SERVER=https://${MACH}:8443

$EXEPATH/jobsub_submit.py --group nova --debug \
       --jobsub-server $SERVER \
            -e SERVER --nowrapfile  file://"$@"

$EXEPATH/jobsub_submit.py --group nova \
       --jobsub-server $SERVER \
           -g -e SERVER --nowrapfile  file://"$@"
