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
cp 8999.sh ${GROUP}_8999.sh
$EXEPATH/jobsub_submit.py $GROUP_SPEC --debug \
       $SERVER_SPEC $SUBMIT_FLAGS \
            -e SERVER --subgroup test  file://${GROUP}_8999.sh 
R=$?
rm ${GROUP}_8999.sh
exit $R

