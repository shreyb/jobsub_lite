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
mkdir -p $GROUP
cd $GROUP
$EXEPATH/jobsub_fetchlog.py --group THIS_GROUP_MUST_FAIL $SERVER_SPEC --jobid 10.0@${MACH} 
cd -
