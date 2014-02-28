#!/bin/sh 
SERVER=$1
export GROUP=nova
if [ "$SERVER" = "" ]; then
    echo "usage: $0 servername"
    run integration tests on servername
    exit 0
fi
echo test simple submission
RSLT=`./simple_submit.sh $SERVER simple_worker_script.sh 1`
echo "$RSLT"
JID=`echo "$RSLT" | grep 'submitted to cluster' | awk '{print $NF}'`
GOTJID=`echo $JID| grep '[0-9].*'`
SUBMIT_WORKED=$?
echo testing dropbox functionality
./test_dropbox_submit.sh $SERVER simple_worker_script.sh 1
echo test helpfile
./test_help.sh $SERVER
echo test listing jobs
./test_listjobs.sh $SERVER
echo test condor_history
echo NOT IMPLEMENTED
echo test retrieving zip_file from sandbox
./retrieve_sandbox.sh $SERVER $JID
