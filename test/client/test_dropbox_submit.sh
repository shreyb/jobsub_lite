#!/bin/sh

if [ "$1" = "" ]; then
    echo "usage $0 \$JOBSUB_SERVER "
    echo "test submission using permutations of --tar_file_name"
    exit 0
fi
source ./setup_env.sh
if [ ! -d "${GROUP}_stuff" ]; then
  mkdir -p ${GROUP}_stuff
fi

#DEBUG="--debug"
DEBUG=''

if [ "$SLEEPVAL" = "" ]; then
    export SLEEPVAL=10  #job sleeps 10 minutes by default
fi

cp simple_worker_script.sh ${GROUP}_dropbox.sh
cp test*.sh ${GROUP}_stuff

export SERVER=https://${MACH}:8443

echo test --tar_file_name with pnfs, creating tarball
$EXEPATH/jobsub_submit.py $GROUP_SPEC $DEBUG \
       $SERVER_SPEC $SUBMIT_FLAGS \
              --tar_file_name tardir://${GROUP}_stuff file://"${GROUP}_dropbox.sh" $SLEEPVAL
T1=$? && TS=$T1
test $TS -eq 0 && echo PASSED
test $TS -ne 0 && echo FAILED

echo test --tar_file_name with pnfs, re-using  tarball
$EXEPATH/jobsub_submit.py $GROUP_SPEC $DEBUG \
       $SERVER_SPEC $SUBMIT_FLAGS \
              --tar_file_name dropbox://${GROUP}_stuff.tar \
            -e SERVER   file://"${GROUP}_dropbox.sh"
T2=$? && TS=$T2
test $TS -eq 0 && echo PASSED
test $TS -ne 0 && echo FAILED

echo test --tar_file_name with RCDS, creating tarball
$EXEPATH/jobsub_submit $GROUP_SPEC $DEBUG \
       $SERVER_SPEC $SUBMIT_FLAGS \
       --use-cvmfs-dropbox \
              --tar_file_name tardir://${GROUP}_stuff file://"${GROUP}_dropbox.sh" $SLEEPVAL
T3=$? && TS=$T3
test $TS -eq 0 && echo PASSED
test $TS -ne 0 && echo FAILED

echo test --tar_file_name with RCDS, reusing tarball
ERROUT=${GROUP}_dropbox.sh.err
rm -f $ERROUT
$EXEPATH/jobsub_submit $GROUP_SPEC $DEBUG \
       $SERVER_SPEC $SUBMIT_FLAGS \
        --use-cvmfs-dropbox \
              --tar_file_name dropbox://${GROUP}_stuff.tar \
            -e SERVER   file://"${GROUP}_dropbox.sh" > $ERROUT

T4=$? && TS=$T4
test $TS -eq 0 && echo PASSED
test $TS -ne 0 && echo FAILED

JID=`grep 'se job id' $ERROUT | awk '{print $4}'`

echo  test that TAR_FILE_NAME is in the job classad
# issue 24327
$EXEPATH/jobsub_q $GROUP_SPEC  \
       $SERVER_SPEC  \
        --jobid $JID --long >>$ERROUT

grep -q TAR_FILE_NAME $ERROUT
T7=$? && TS=$T7
test $TS -eq 0 && echo PASSED
test $TS -ne 0 && echo FAILED

echo  test jobsub_q --better-analyze
# issue 24057 'smoke test'
$EXEPATH/jobsub_q $GROUP_SPEC  \
       $SERVER_SPEC  \
        --jobid $JID --better-analyze  >>$ERROUT
grep -q 'for your job reduces to these conditions' $ERROUT
T10=$? && TS=$T10
test $TS -eq 0 && echo PASSED
test $TS -ne 0 && echo FAILED

echo test using -tar_file_name instead of --tar_file_name, submission should fail
ERROUT=${GROUP}_dropbox2.sh.err
rm -f $ERROUT
$EXEPATH/jobsub_submit $GROUP_SPEC  \
       $SERVER_SPEC $SUBMIT_FLAGS \
        --use-cvmfs-dropbox \
              -tar_file_name dropbox://${GROUP}_stuff.tar \
            -e SERVER   file://"${GROUP}_dropbox.sh" >$ERROUT
ret=$?
test $ret -ne 0
T5=$?
grep -q 'unrecognized arguments: -tar_file_name' $ERROUT
T6=$?
test $T5 -eq 0 && test $T6 -eq 0
TS=$?
test $TS -eq 0 && echo PASSED
test $TS -ne 0 && echo FAILED

#issue 23380
echo test that role MARS forbidden to --use-cvmfs-dropbox, submission should fail
ERROUT=${GROUP}_dropbox3.sh.err
rm -f $ERROUT
$EXEPATH/jobsub_submit $GROUP_SPEC  \
       $SERVER_SPEC $SUBMIT_FLAGS \
        --use-cvmfs-dropbox  --role MARS \
              -tar_file_name dropbox://${GROUP}_stuff.tar \
            -e SERVER   file://"${GROUP}_dropbox.sh" >$ERROUT
ret=$?
test $ret -ne 0
T8=$?
grep -q 'role mars are not allowed to use --use-cvmfs-dropbox' $ERROUT
T9=$?
test $T8 -eq 0 && test $T9 -eq 0
TS=$?
test $TS -eq 0 && echo PASSED
test $TS -ne 0 && echo FAILED

! (( $T1 || $T2 || $T3 || $T4 || $T5 || $T6 || $T7 || $T8 || $T9 ))
ALL_TESTS_WORKED=$?
echo $0 exiting with status $ALL_TESTS_WORKED
exit $ALL_TESTS_WORKED
