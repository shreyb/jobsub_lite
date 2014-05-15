#!/bin/sh 
SERVER=$1
if [ "$SERVER" = "" ]; then
    echo "usage: $0 servername"
    echo "run integration tests on servername"
    exit 0
fi
echo test simple submission
RSLT=`sh ${TEST_FLAG} ./simple_submit.sh $SERVER simple_worker_script.sh 1`
echo "$RSLT" >$1.submit.log 2>1&
JID=`echo "$RSLT" | grep 'Use job id' | awk '{print $4}'`
GOTJID=`echo $JID| grep '[0-9].0@'`
SUBMIT_WORKED=$?
if [ "$SUBMIT_WORKED" = "0" ]; then
     echo "successfully submitted job $GOTJID"
else
    echo "submission problem, please see file $1.submit.log"
fi 

echo test submission with role
RSLT2=`sh ${TEST_FLAG} ./simple_submit_with_role.sh $SERVER simple_worker_script.sh 1` 
echo "$RSLT2" >$1.submit_role.log 2>1&
JID2=`echo "$RSLT2" | grep 'Use job id' | awk '{print $4}'`
GOTJID2=`echo $JID2| grep '[0-9].0@'`
SUBMIT_WORKED2=$?
if [ "$SUBMIT_WORKED2" = "0" ]; then
     echo "successfully submitted job $GOTJID2"
else
    echo "submission problem, please see file $1.submit_role.log"
fi 
echo testing holding and releasing
sh ${TEST_FLAG} ./test_hold_release.sh $SERVER $GOTJID2 >$1.holdrelease.log 2>&1

echo testing dropbox functionality
sh ${TEST_FLAG} ./test_dropbox_submit.sh $SERVER simple_worker_script.sh >$1.dropbox.log 2>&1
echo test helpfile
sh ${TEST_FLAG} ./test_help.sh $SERVER >$1.help.log 2>&1
echo test listing jobs
sh ${TEST_FLAG} ./test_listjobs.sh $SERVER $GOTJID2 >$1.list.log 2>&1
echo test condor_history
sh ${TEST_FLAG} ./test_history.sh $SERVER $GOTJID2 >$1.history.log 2>&1
echo test retrieving zip_file from sandbox
sh ${TEST_FLAG} ./retrieve_sandbox.sh $SERVER $GOTJID22 >$1.sandbox.log 2>&1
echo testing removing job
sh ${TEST_FLAG} ./test_rm.sh  $SERVER $GOTJID2 >$1.testrm.log  2>&1
