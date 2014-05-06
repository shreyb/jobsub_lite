#!/bin/sh

if [ "$1" = "" ]; then
    echo "usage $0 server script_to_submit [script args]"
    echo "test submission to jobsub client/server architecture"
    exit 0
fi
source ./setup_env.sh
tar cfv stuff.tar * > /dev/null

export SERVER=https://${MACH}:8443

$EXEPATH/jobsub_submit.py --group $GROUP --debug \
       $SERVER_SPEC \
              dropbox://stuff.tar \
            -e SERVER --nowrapfile  file://"$@"
rm stuff.tar

