#!/bin/sh

if [ "$1" = "" ]; then
    echo "usage $0 server script_to_submit [script args]"
    echo "test submission to jobsub client/server architecture"
    exit 0
fi
source ./setup_env.sh
if [ ! -e "stuff2.tar" ] ; then
    tar cfv stuff2.tar * > /dev/null
fi
#DEBUG="--debug"
export SERVER=https://${MACH}:8443

$EXEPATH/jobsub_submit.py $GROUP_SPEC $DEBUG \
       $SERVER_SPEC $SUBMIT_FLAGS \
               -f dropbox://${GROUP}_stuff.tar \
               -f dropbox://stuff2.tar \
            -e SERVER  file://"$@"
SUBMIT_WORKED=$?
echo $0 exiting with status $SUBMIT_WORKED
exit $SUBMIT_WORKED
