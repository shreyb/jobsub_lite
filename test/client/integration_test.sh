#!/bin/sh 
SERVER=$1
if [ "$SERVER" = "" ]; then
    echo "usage: $0 servername"
    echo "run integration tests on servername"
    exit 0
fi
echo test simple submission
RSLT=`./simple_submit.sh $SERVER simple_worker_script.sh 1`
echo "$RSLT" >$1.submit.log 2>1&
JID=`echo "$RSLT" | grep 'submitted to cluster' | awk '{print $NF}'`
GOTJID=`echo $JID| grep '[0-9].*'`
SUBMIT_WORKED=$?
if [ "$SUBMIT_WORKED" = "0" ]; then
     echo "successfully submitted job $GOTJID"
else
    echo "submission problem, please see file $1.submit.log"
fi 

echo test submission with role
RSLT2=`./simple_submit_with_role.sh $SERVER simple_worker_script.sh 1` 
echo "$RSLT2" >$1.submit_role.log 2>1&
JID2=`echo "$RSLT2" | grep 'submitted to cluster' | awk '{print $NF}'`
GOTJID2=`echo $JID2| grep '[0-9].*'`
SUBMIT_WORKED2=$?
if [ "$SUBMIT_WORKED2" = "0" ]; then
     echo "successfully submitted job $GOTJID2"
else
    echo "submission problem, please see file $1.submit_role.log"
fi 
echo testing holding and releasing
./test_hold_release.sh $SERVER $GOTJID2 >$1.holdrelease.log 2>1&

echo testing removing job
./test_rm.sh  $SERVER $GOTJID2 >$1.testrm.log  2>1&
echo testing dropbox functionality
./test_dropbox_submit.sh $SERVER simple_worker_script.sh >$1.dropbox.log 2>1&
echo test helpfile
./test_help.sh $SERVER >$1.help.log 2>1&
echo test listing jobs
./test_listjobs.sh $SERVER >$1.list.log 2>1&
echo test condor_history
echo NOT IMPLEMENTED
echo test retrieving zip_file from sandbox
./retrieve_sandbox.sh $SERVER $JID >$1.sandbox.log 2>1&
