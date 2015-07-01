#!/bin/sh

if [ "$1" = "" ]; then
    echo "usage $0 server script_to_submit [script args]"
    echo "test submission to jobsub client/server architecture"
    exit 0
fi
source ./setup_env.sh
if [ ! -e "stuff.tar" ]; then
  tar cfv stuff.tar * > /dev/null
fi

export SERVER=https://${MACH}:8443

$EXEPATH/jobsub_submit.py $GROUP_SPEC --debug \
       $SERVER_SPEC $SUBMIT_FLAGS \
              --tar_file_name dropbox://stuff.tar \
            -e SERVER --nowrapfile  file://"$@"
SUBMIT_WORKED=$?
#rm stuff.tar
echo $0 exiting with status $SUBMIT_WORKED
exit $SUBMIT_WORKED
