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
cp 7072.sh ${GROUP}_7072.sh
$EXEPATH/jobsub_submit.py $GROUP_SPEC --debug \
       $SERVER_SPEC $SUBMIT_FLAGS \
            -e SERVER --nowrapfile   file://${GROUP}_7072.sh 7000000
R=$?
rm ${GROUP}_7072.sh
exit $R

