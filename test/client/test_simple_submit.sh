#!/bin/sh

if [ "$1" = "" ]; then
    echo "usage $0 server script_to_submit [script args]"
    echo "test submission to jobsub client/server architecture"
    exit 0
fi
source ./setup_env.sh

export SERVER=https://${MACH}:8443

$EXEPATH/jobsub_submit.py --group $GROUP --debug \
       $SERVER_SPEC  $SUBMIT_FLAGS \
            -e SERVER   file://"$@"
T1=$?

$EXEPATH/jobsub_submit.py --group $GROUP \
       $SERVER_SPEC $SUBMIT_FLAGS \
           -g -e SERVER   file://"$@"
T2=$?

! (( $T1 || $T2 ))
T3=$?
echo $0 exiting with status $T3
exit $T3

