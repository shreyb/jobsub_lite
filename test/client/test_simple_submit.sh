#!/bin/sh

if [ "$1" = "" ]; then
    echo "usage $0 server script_to_submit [script args]"
    echo "test submission to jobsub client/server architecture"
    exit 0
fi
source ./setup_env.sh

export SERVER=https://${MACH}:8443

$EXEPATH/jobsub_submit.py $GROUP_SPEC --debug \
       $SERVER_SPEC  $SUBMIT_FLAGS \
            -e SERVER   file://"$@"
T1=$?

$EXEPATH/jobsub_submit.py $GROUP_SPEC \
       $SERVER_SPEC $SUBMIT_FLAGS \
           -g -e SERVER   file://"$@"
T2=$?

! (( $T1 || $T2 ))
TFINAL=$?
echo $0 exiting with status $TFINAL
exit $TFINAL

