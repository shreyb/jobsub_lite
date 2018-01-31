#!/bin/sh

if [ "$1" = "" ]; then
    echo "usage $0 server script_to_submit [script args]"
    echo "test submission to jobsub client/server architecture"
    exit 0
fi
source ./setup_env.sh
if [ ! -d "${GROUP}_stuff" ]; then
  mkdir -p ${GROUP}_stuff
fi

#DEBUG="--debug"

cp simple_worker_script.sh ${GROUP}_dropbox.sh
cp test*.sh ${GROUP}_stuff

export SERVER=https://${MACH}:8443

$EXEPATH/jobsub_submit.py $GROUP_SPEC $DEBUG \
       $SERVER_SPEC $SUBMIT_FLAGS \
              --tar_file_name tardir://${GROUP}_stuff file://"${GROUP}_dropbox.sh"
T1=$?
echo T1:$T1
$EXEPATH/jobsub_submit.py $GROUP_SPEC $DEBUG \
       $SERVER_SPEC $SUBMIT_FLAGS \
              --tar_file_name dropbox://${GROUP}_stuff.tar \
            -e SERVER   file://"${GROUP}_dropbox.sh"
T2=$?
echo T2:$T2
! (( $T1 || $T2 ))
SUBMIT_WORKED=$?
echo $0 exiting with status $SUBMIT_WORKED
exit $SUBMIT_WORKED
