#!/bin/sh

if [ "$1" = "" ]; then
    echo "usage $0 server script_to_submit [script args]"
    echo "test submission to jobsub client/server architecture"
    exit 0
fi
cd ..
source ./setup_env.sh
cd -

STOPFILE=$HOME/stop_load_test
T1=0
LOG=`pwd`/${GROUP}_dag.log
echo '' > $LOG
cd ../jobsubDagTest
while [[ ! -e "$STOPFILE"  && "$T1" = "0" ]]
do
        $EXEPATH/jobsub_submit_dag  --role Production  $GROUP_SPEC $SUBMIT_FLAGS \
           --debug $SERVER_SPEC  file://dagTest  --maxConcurrent 3 >> $LOG 2>&1
        T1=$?
        if [ "$T1" != "0" ]; then
            /bin/echo "$LOG" >> $STOPFILE
        fi
done
rm -f ${GROUP}_pro.sh
echo ${GROUP} submits exiting with status $T1
exit $T1
