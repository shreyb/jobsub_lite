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
cp 6561.sh ${GROUP}_6561.sh
$EXEPATH/jobsub_submit.py $GROUP_SPEC --debug \
       $SERVER_SPEC $SUBMIT_FLAGS \
            -e SERVER --nowrapfile   file://${GROUP}_6561.sh foo@bar.com
T1=$?
$EXEPATH/jobsub_submit.py $GROUP_SPEC \
       $SERVER_SPEC $SUBMIT_FLAGS \
           -g -e SERVER    file://${GROUP}_6561.sh foo@bar.com
T2=$?

rm ${GROUP}_6561.sh
! (( $T1 || $T2 ))
TT=$?
exit $TT
