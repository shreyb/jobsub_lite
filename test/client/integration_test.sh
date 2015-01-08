#!/bin/sh 

function lg_echo {
  echo "$@"
  echo "$@" >> $TESTLOGFILE
}



function pass_or_fail {

if [ "$?" == "0" ]; then
    grep -i exception $OUTFILE 
    if [ "$?" = "0" ]; then
    	lg_echo "FAILED"
    else
	lg_echo "PASSED"
    fi
else
    lg_echo "FAILED"
fi
}


SERVER=$1
export TESTLOGFILE=$SERVER.testlog

if [ "$SERVER" = "" ]; then
    lg_echo "usage: $0 servername"
    lg_echo "run integration tests on servername"
    exit 0
fi
if [[ "$GROUP" = "" && "$JOBSUB_GROUP" = "" ]]; then
    export GROUP=nova
fi
if [ "$GROUP" = "cdf" ]; then
    export SUBMIT_FLAGS=" $SUBMIT_FLAGS --tar_file_name dropbox://junk.tgz -N 2 "
fi
if [ "$GROUP" != "" ]; then
    export OUTGROUP=$GROUP
fi
if [ "$JOBSUB_GROUP" != "" ]; then
    export OUTGROUP=$JOBSUB_GROUP
fi

lg_echo test simple submission
OUTFILE=$1.submit.$OUTGROUP.log
sh ${TEST_FLAG} ./test_simple_submit.sh $SERVER simple_worker_script.sh 1 >$OUTFILE 2>&1
JID=`grep 'se job id' $OUTFILE | awk '{print $4}'`
GOTJID=`echo $JID| grep '[0-9].0@'`
SUBMIT_WORKED=$?
if [ "$SUBMIT_WORKED" = "0" ]; then
     lg_echo "successfully submitted job $GOTJID"
else
    lg_echo "submission problem, please see file $1.submit.$OUTGROUP.log"
fi 

lg_echo test submission with role
OUTFILE=$1.submit_role.$OUTGROUP.log
sh ${TEST_FLAG} ./test_simple_submit_with_role.sh $SERVER simple_worker_script.sh 1 >$OUTFILE 2>&1
JID2=`grep 'se job id' $OUTFILE | awk '{print $4}'`
GOTJID2=`echo $JID2| grep '[0-9].0@'`
SUBMIT_WORKED2=$?
if [ "$SUBMIT_WORKED2" = "0" ]; then
     lg_echo "PASSED successfully submitted job $GOTJID2"
else
    lg_echo "FAILED submission problem, please see file $1.submit_role.$OUTGROUP.log"
fi 
lg_echo testing holding and releasing
OUTFILE=$1.holdrelease.$OUTGROUP.log
sh ${TEST_FLAG} ./test_hold_release.sh $SERVER $GOTJID2 >$OUTFILE 2>&1
pass_or_fail
lg_echo testing dag submission 
OUTFILE=$1.testdag.$OUTGROUP.log
sh ${TEST_FLAG} ./test_dag_submit.sh  $SERVER  >$OUTFILE  2>&1
pass_or_fail
lg_echo testing dag with role submission 
OUTFILE=$1.testdag.role.$OUTGROUP.log
sh ${TEST_FLAG} ./test_dag_submit_with_role.sh  $SERVER  >$OUTFILE  2>&1
pass_or_fail
lg_echo testing cdf sam job
cd cdf_dag_test
OUTFILE="../$1.test_cdf_sam_job.log"
sh ${TEST_FLAG} ./cdf_sam_test.sh $SERVER >$OUTFILE 2>&1
pass_or_fail
JID3=`grep 'se job id' $OUTFILE | awk '{print $4}'`
GOTJID3=`echo $JID2| grep '[0-9].0@'`
cd -
lg_echo testing dropbox functionality
OUTFILE=$1.dropbox.$OUTGROUP.log
sh ${TEST_FLAG} ./test_dropbox_submit.sh $SERVER simple_worker_script.sh >$OUTFILE 2>&1
pass_or_fail
lg_echo test helpfile
OUTFILE=$1.help.$OUTGROUP.log 
sh ${TEST_FLAG} ./test_help.sh $SERVER >$OUTFILE 2>&1
pass_or_fail
lg_echo test listing jobs
OUTFILE=$1.list.$OUTGROUP.log
sh ${TEST_FLAG} ./test_listjobs.sh $SERVER $GOTJID2 >$OUTFILE 2>&1
pass_or_fail
lg_echo 'test listing --long jobs'
OUTFILE=$1.listlong.$OUTGROUP.log
sh ${TEST_FLAG} ./test_listjobs_long.sh $SERVER $GOTJID2 >$OUTFILE 2>&1
pass_or_fail
lg_echo 'test listing --dag jobs'
OUTFILE=$1.listdag.$OUTGROUP.log
sh ${TEST_FLAG} ./test_listjobs_dag.sh $SERVER $GOTJID2 >$OUTFILE 2>&1
pass_or_fail
lg_echo test condor_history
OUTFILE=$1.history.$OUTGROUP.log
sh ${TEST_FLAG} ./test_history.sh $SERVER $GOTJID2 > $OUTFILE 2>&1
pass_or_fail
lg_echo test retrieving zip_file from sandbox
OUTFILE=$1.sandbox.$OUTGROUP.log
sh ${TEST_FLAG} ./retrieve_sandbox.sh $SERVER $GOTJID2 >$OUTFILE 2>&1
pass_or_fail
lg_echo testing removing job
OUTFILE=$1.testrm.$OUTGROUP.log
sh ${TEST_FLAG} ./test_rm.sh  $SERVER $GOTJID2 >$OUTFILE  2>&1
pass_or_fail
lg_echo testing list-sandboxes 
OUTFILE=$1.testlistsandboxes.$OUTGROUP.log
sh ${TEST_FLAG} ./test_listsandboxes.sh  $SERVER >$OUTFILE  2>&1
pass_or_fail
lg_echo testing list-sites 
OUTFILE=$1.testlist-sites.$OUTGROUP.log
sh ${TEST_FLAG} ./test_status.sh  $SERVER >$OUTFILE  2>&1
pass_or_fail
./api_coverage_test.sh MACH=$SERVER GROUP=$GROUP
for bug in `ls bug_tests`; do cd bug_tests/$bug ;   ./${bug}_test.sh $SERVER >${bug}.out 2>&1 ;  ./${bug}_report.sh; cd ../.. ; done
