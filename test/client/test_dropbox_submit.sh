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

DEBUG="--debug"
if [ "$SLEEPVAL" = "" ]; then
    export SLEEPVAL=10  #job sleeps 10 minutes by default
fi

cp simple_worker_script.sh ${GROUP}_dropbox.sh
cp test*.sh ${GROUP}_stuff

export SERVER=https://${MACH}:8443

#test --tar_file_name with pnfs, creating tarball
$EXEPATH/jobsub_submit.py $GROUP_SPEC $DEBUG \
       $SERVER_SPEC $SUBMIT_FLAGS \
              --tar_file_name tardir://${GROUP}_stuff file://"${GROUP}_dropbox.sh" $SLEEPVAL
T1=$?
echo T1:$T1

#test --tar_file_name with pnfs, re-using  tarball
$EXEPATH/jobsub_submit.py $GROUP_SPEC $DEBUG \
       $SERVER_SPEC $SUBMIT_FLAGS \
              --tar_file_name dropbox://${GROUP}_stuff.tar \
            -e SERVER   file://"${GROUP}_dropbox.sh"
T2=$?
echo T2:$T2

#test --tar_file_name with RCDS, creating tarball
$EXEPATH/jobsub_submit $GROUP_SPEC $DEBUG \
       $SERVER_SPEC $SUBMIT_FLAGS \
       --use-cvmfs-dropbox \
              --tar_file_name tardir://${GROUP}_stuff file://"${GROUP}_dropbox.sh" $SLEEPVAL
T3=$?
echo T3:$T3

#test --tar_file_name with RCDS, reusing tarball
ERROUT=${GROUP}_dropbox.sh.err
rm -f $ERROUT
$EXEPATH/jobsub_submit $GROUP_SPEC $DEBUG \
       $SERVER_SPEC $SUBMIT_FLAGS \
        --use-cvmfs-dropbox \
              --tar_file_name dropbox://${GROUP}_stuff.tar \
            -e SERVER   file://"${GROUP}_dropbox.sh" > $ERROUT
T4=$?
echo T4:$T4

JID=`grep 'se job id' $ERROUT | awk '{print $4}'`

# test that TAR_FILE_NAME is in the job classad
# issue 24327
$EXEPATH/jobsub_q $GROUP_SPEC  \
       $SERVER_SPEC  \
        --jobid $JID --long >>$ERROUT

grep -q TAR_FILE_NAME $ERROUT
T7=$?
echo T7:$T7

#test using -tar_file_name instead of --tar_file_name
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
echo T5:$T5
grep -q 'looks like you specified' $ERROUT
T6=$?

! (( $T1 || $T2 || $T3 || $T4 || $T5 || $T6 || $T7 ))
ALL_TESTS_WORKED=$?
echo $0 exiting with status $ALL_TESTS_WORKED
exit $ALL_TESTS_WORKED
