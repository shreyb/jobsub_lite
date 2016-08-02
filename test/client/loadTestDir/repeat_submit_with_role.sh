#!/bin/sh

if [ "$1" = "" ]; then
    echo "usage $0 server script_to_submit [script args]"
    echo "test submission to jobsub client/server architecture"
    exit 0
fi
cd ..
source ./setup_env.sh
cd -
if [ "$1" = "" ]; then
    export JOB=../simple_worker_script.sh
else
    export JOB=$1
fi
shift
cp $JOB ${GROUP}_pro.sh
echo '' >  ${GROUP}_sub.log
STOPFILE=$HOME/stop_load_test
T1=0

while [[ ! -e "$STOPFILE"  && "$T1" = "0" ]]
do
        $EXEPATH/jobsub_submit --role=Production $GROUP_SPEC  \
            $SERVER_SPEC $SUBMIT_FLAGS \
                -g  -e SERVER  file://${GROUP}_pro.sh "$@" >> ${GROUP}_sub.log 2>&1
        T1=$?
        if [ "$T1" != "0" ]; then
            /bin/echo "${PWD}/${GROUP}_sub.log" >> $STOPFILE
        fi
done
rm -f ${GROUP}_pro.sh
echo ${GROUP} submits exiting with status $T1
exit $T1
