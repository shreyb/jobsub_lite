#!/bin/sh

if [ "$1" = "" ]; then
    echo "usage $0 server script_to_submit [script args]"
    echo "test submission to jobsub client/server architecture"
    exit 0
fi
cd ../../
source ./setup_env.sh
cd -
export FOO='this should show up in worker node environment'
export SERVER=https://${MACH}:8443
cp 7400.sh ${GROUP}_7400.sh
$EXEPATH/jobsub_submit.py $GROUP_SPEC --debug \
       $SERVER_SPEC $SUBMIT_FLAGS \
            -e SERVER --environment=FOO   file://${GROUP}_7400.sh 
T1=$?


export FOO='BAR=BAZ'
$EXEPATH/jobsub_submit.py $GROUP_SPEC --debug \
       $SERVER_SPEC $SUBMIT_FLAGS \
                   -e SERVER --environment=FOO   file://${GROUP}_7400.sh
T2=$?

rm ${GROUP}_7400.sh

! (( $T1 || $T2 ))
TT=$?
exit $TT
