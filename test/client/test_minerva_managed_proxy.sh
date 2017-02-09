#!/bin/sh 

export TEST_FLAG=" -x "
export OTHER_FLAGS=" --debug "
export OTHER_TEST_FLAGS=" --role Production $OTHER_TEST_FLAGS"
export SUBMIT_FLAGS=" --role Production $SUBMIT_FLAGS"
export X509_USER_PROXY=/opt/minervapro/minerva.Production.proxy
export GROUP=minerva
export OUTGROUP=minerva.Production

function lg_echo {
  echo "$@"
  echo "$@" >> $TESTLOGFILE
}



function pass_or_fail {

if [ "$?" == "0" ]; then
    grep -i ' exception' $OUTFILE 
    if [ "$?" = "0" ]; then
    	lg_echo "FAILED"
        if [ "$JOBSUB_TEST_CONTINUE_ON_FAILURE" = "" ]; then
            exit 1
        fi
    else
	lg_echo "PASSED"
    fi
else
    lg_echo "FAILED"
    if [ "$JOBSUB_TEST_CONTINUE_ON_FAILURE" = "" ]; then
        exit 1
    fi
fi
}


export SERVER=$1
if [ -e "$2" ]; then
    source $2
fi

export TESTLOGFILE=$SERVER.testlog

if [ "$SERVER" = "" ]; then
    lg_echo "usage: $0 servername"
    lg_echo "run integration tests on servername"
    exit 0
fi


if [ "$JOBSUB_GROUP" != "" ]; then
    export OUTGROUP=$JOBSUB_GROUP
fi
if [ "$USE_UPS_DIR" != "" ]; then
    source $USE_UPS_DIR
fi
if [ "$USE_JOBSUB_CLIENT_VERSION" != "" ]; then
    setup jobsub_client $USE_JOBSUB_CLIENT_VERSION
fi

lg_echo test a verbose job to test output file truncation
OUTFILE=$1.noisy.$OUTGROUP.log
sh ${TEST_FLAG} ./test_noisy_job.sh $SERVER >$OUTFILE 2>&1
T1=$?
JID=`grep 'se job id' $OUTFILE | awk '{print $4}'`
T2=$?
NOISYJID=`echo $JID| grep '[0-9].0@'`
T3=$?
test $T1 -eq 0 -a $T2 -eq 0 -a $T3 -eq 0
SUBMIT_WORKED=$?
if [ "$SUBMIT_WORKED" = "0" ]; then
     lg_echo "successfully submitted job $NOISYJID"
else
    lg_echo "submission problem, please see file $OUTFILE"
fi 
test $SUBMIT_WORKED -eq 0
pass_or_fail

lg_echo test simple submission
OUTFILE=$1.submit.$OUTGROUP.log
cp simple_worker_script.sh ${GROUP}_test.sh
sh ${TEST_FLAG} ./test_simple_submit.sh $SERVER ${GROUP}_test.sh 1 >$OUTFILE 2>&1
T1=$?
rm ${GROUP}_test.sh
JID=`grep 'se job id' $OUTFILE | awk '{print $4}'`
T2=$?
GOTJID=`echo $JID| grep '[0-9].0@'`
T3=$?
test $T1 -eq 0 -a $T2 -eq 0 -a $T3 -eq 0
SUBMIT_WORKED=$?
if [ "$SUBMIT_WORKED" = "0" ]; then
     lg_echo "successfully submitted job $GOTJID"
else
    lg_echo "submission problem, please see file $OUTFILE"
fi 
test $SUBMIT_WORKED -eq 0
pass_or_fail
lg_echo testing holding and releasing $GROUP jobs owned by $USER
OUTFILE=$1.holdrelease.byuser.$OUTGROUP.log
sh ${TEST_FLAG} ./test_hold_release_byuser.sh $SERVER $GOTJID >$OUTFILE 2>&1
pass_or_fail
lg_echo testing holding and releasing
OUTFILE=$1.holdrelease.$OUTGROUP.log
sh ${TEST_FLAG} ./test_hold_release.sh $SERVER $GOTJID >$OUTFILE 2>&1
pass_or_fail
if [ "$SKIP_PRODUCTION_TEST" = "" ]; then
    lg_echo test submission with role
    OUTFILE=$1.submit_role.$OUTGROUP.log
    sh ${TEST_FLAG} ./test_simple_submit_with_role.sh $SERVER simple_worker_script.sh 1 >$OUTFILE 2>&1
    T1=$?
    JID2=`grep 'se job id' $OUTFILE | awk '{print $4}'`
    T2=$?
    GOTJID2=`echo $JID2| grep '[0-9].0@'`
    T3=$?
    test $T1 -eq 0 -a $T2 -eq 0 -a $T3 -eq 0
    SUBMIT_WORKED2=$?
    if [ "$SUBMIT_WORKED2" = "0" ]; then
         lg_echo "PASSED successfully submitted job $GOTJID2"
    else
         lg_echo "FAILED submission problem, please see file $OUTFILE"
    fi 
    test $SUBMIT_WORKED2 -eq 0
    pass_or_fail
    lg_echo testing holding and releasing with role
    OUTFILE=$1.holdrelease.role.$OUTGROUP.log
    sh ${TEST_FLAG} ./test_hold_release_role.sh $SERVER $GOTJID2 >$OUTFILE 2>&1
    pass_or_fail
    GUSER=${GROUP}pro
    lg_echo testing holding and releasing $GROUP jobs owned by $GUSER
    OUTFILE=$1.holdrelease.byuser.role$OUTGROUP.log
    sh ${TEST_FLAG} ./test_hold_release_byuser_role.sh $SERVER $GOTJID >$OUTFILE 2>&1
    pass_or_fail
fi
lg_echo testing dag submission 
OUTFILE=$1.testdag.$OUTGROUP.log
sh ${TEST_FLAG} ./test_dag_submit.sh  $SERVER  >$OUTFILE  2>&1
pass_or_fail
DAGJID=`grep 'se job id' $OUTFILE | awk '{print $4}'`
echo use $DAGJID to retrieve dag submission results
if [ "$SKIP_PRODUCTION_TEST" = "" ]; then
    lg_echo testing dag with role submission 
    OUTFILE=$1.testdag.role.$OUTGROUP.log
    sh ${TEST_FLAG} ./test_dag_submit_with_role.sh  $SERVER  >$OUTFILE  2>&1
    pass_or_fail
    DAGROLEJID=`grep 'se job id' $OUTFILE | awk '{print $4}'`
    echo use $DAGROLEJID to retrieve dag submission results
fi

lg_echo test --maxConcurrent submit
OUTFILE=$1.maxConcurrent.$OUTGROUP.log
cp simple_worker_script.sh ${GROUP}_maxConcurrent.sh
sh ${TEST_FLAG} ./test_maxConcurrent_submit.sh $SERVER ${GROUP}_maxConcurrent.sh 1 >$OUTFILE 2>&1
pass_or_fail
MAXCONCURRENTJID=`grep 'se job id' $OUTFILE | awk '{print $4}'`
echo use $MAXCONCURRENTJID to retrieve maxconncurent results
rm ${GROUP}_maxConcurrent.sh
lg_echo testing dropbox functionality
OUTFILE=$1.dropbox.$OUTGROUP.log
cp simple_worker_script.sh ${GROUP}_dropbox.sh
sh ${TEST_FLAG} ./test_dropbox_submit.sh $SERVER ${GROUP}_dropbox.sh >$OUTFILE 2>&1
pass_or_fail

lg_echo testing dropbox with multiple -f functionality
cp ${GROUP}_dropbox.sh ${GROUP}_minus_f.sh
OUTFILE=$1.dropbox_minus_f.$OUTGROUP.log
sh ${TEST_FLAG} ./test_dropbox_minus_f_submit.sh $SERVER ${GROUP}_minus_f.sh >$OUTFILE 2>&1
pass_or_fail
rm ${GROUP}_minus_f.sh
lg_echo test helpfile
OUTFILE=$1.help.$OUTGROUP.log 
sh ${TEST_FLAG} ./test_help.sh $SERVER >$OUTFILE 2>&1
pass_or_fail

lg_echo test listing jobs
OUTFILE=$1.list.$OUTGROUP.log
sh ${TEST_FLAG} ./test_listjobs.sh $SERVER $GOTJID >$OUTFILE 2>&1
pass_or_fail

lg_echo 'test listing --long jobs'
OUTFILE=$1.listlong.$OUTGROUP.log
sh ${TEST_FLAG} ./test_listjobs_long.sh $SERVER $GOTJID >$OUTFILE 2>&1
pass_or_fail

lg_echo 'test listing --dag jobs'
OUTFILE=$1.listdag.$OUTGROUP.log
sh ${TEST_FLAG} ./test_listjobs_dag.sh $SERVER $GOTJID >$OUTFILE 2>&1
pass_or_fail

lg_echo test condor_history
OUTFILE=$1.history.$OUTGROUP.log
sh ${TEST_FLAG} ./test_history.sh $SERVER $GOTJID > $OUTFILE 2>&1
pass_or_fail

lg_echo test retrieving zip_file from sandbox 
OUTFILE=$1.sandbox.$OUTGROUP.log
sh ${TEST_FLAG} ./test_retrieve_sandbox.sh $SERVER $GOTJID  >$OUTFILE 2>&1
pass_or_fail

if [ "$SKIP_PRODUCTION_TEST" = "" ]; then
    lg_echo test retrieving zip_file from sandbox with role Production
    OUTFILE=$1.sandbox.Production.$OUTGROUP.log
    sh ${TEST_FLAG} ./test_retrieve_sandbox.sh $SERVER $GOTJID2 Production >$OUTFILE 2>&1
    pass_or_fail
fi

lg_echo testing removing job
OUTFILE=$1.testrm.$OUTGROUP.log
sh ${TEST_FLAG} ./test_rm.sh  $SERVER $GOTJID >$OUTFILE  2>&1
pass_or_fail

lg_echo testing list-sandboxes 
OUTFILE=$1.testlistsandboxes.$OUTGROUP.log
sh ${TEST_FLAG} ./test_listsandboxes.sh  $SERVER >$OUTFILE  2>&1
pass_or_fail

lg_echo testing list-sites 
OUTFILE=$1.testlist-sites.$OUTGROUP.log
sh ${TEST_FLAG} ./test_status.sh  $SERVER >$OUTFILE  2>&1
pass_or_fail

OUTFILE=$1.jobsubjobsections.$OUTGROUP.log
for JOB in $DAGJID  $MAXCONCURRENTJID ; do
    lg_echo checking $JOB for JobsubJobSections
    ./test_for_jobsubjobsection.sh $SERVER $JOB >> $OUTFILE  2>&1
    pass_or_fail
done

OUTFILE=$1.cdfjobsubjobsections.$OUTGROUP.log
for JOB in $CDFJID ; do
    lg_echo checking cdf $JOB for JobsubJobSections
    ./test_cdf_jobsubjobsection.sh $SERVER $JOB >> $OUTFILE  2>&1
    pass_or_fail
done

OUTFILE=$1.checklogfiletruncations.$OUTGROUP.log
for JOB in $NOISYJID ; do
    lg_echo checking  $JOB for expected output file truncations
    ./test_for_logfile_truncation.sh $SERVER $JOB >> $OUTFILE  2>&1
    pass_or_fail
done

OUTFILE=$1.api_coverage.$OUTGROUP.log

if [ "$X509_USER_PROXY" = "" ]; then
    X509_USER_PROXY=/tmp/x509up_u${UID}
    if [ ! -e "$X509_USER_PROXY" ]; then
        kx509
    fi
fi 

if [ "$X509_USER_CERT" = "" ]; then
    X509_USER_CERT=$X509_USER_PROXY
    X509_USER_KEY=$X509_USER_PROXY
fi

grep URL ${SERVER}*${GROUP}*log | sed 's/.*https/https/' | sed 's/ .*$//' | sort | uniq -u > ${SERVER}.${GROUP}.urls_covered.log

lg_echo testing api coverage of URLS
sh ${TEST_FLAG} ./api_coverage_test.sh MACH=$SERVER GROUP=$GROUP X509_USER_CERT=$X509_USER_CERT  X509_USER_KEY=$X509_USER_KEY >$OUTFILE 2>&1
RSLT=$?
#grep 'HTTP/1.1' `echo $SERVER | cut -d '.' -f1`*out | cut -d ' ' -f2-4 | sort | uniq -c
tail -6 $OUTFILE
test "$RSLT" = "0"
pass_or_fail

HERE=`pwd`
OUTFILE=$1.bug_tests.$OUTGROUP.log
RSLT=0
for bug in `ls bug_tests`; do cd $HERE/bug_tests/$bug ;  sh ${TEST_FLAG} ./${bug}_test.sh $SERVER > ${bug}.${GROUP}.out 2>&1 ; cat ${bug}.${GROUP}.out >> $OUTFILE ;   ./${bug}_report.sh;  export RSLT=$?;  if [ "$RSLT" != "0" ]; then break ; fi ;   done 
test "$RSLT" = "0"
pass_or_fail
