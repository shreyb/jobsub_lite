#!/bin/sh

if [ "$1" = "" ]; then
    echo "usage $0 server  "
    echo "test submission to jobsub client/server architecture"
    exit 0
fi
source ./setup_env.sh

export SERVER=https://${MACH}:8443

#JOBSUB_MAX_JOBLOG_SIZE
#JOBSUB_MAX_JOBLOG_HEAD_SIZE
#JOBSUB_MAX_JOBLOG_TAIL_SIZE
source ./noisy.env.sh

if [[ "$JOBSUB_MAX_JOBLOG_SIZE" ]]; then
    export SUBMIT_FLAGS="$SUBMIT_FLAGS -e JOBSUB_MAX_JOBLOG_SIZE"
fi

if [[ "$JOBSUB_MAX_JOBLOG_HEAD_SIZE" ]]; then
    export SUBMIT_FLAGS="$SUBMIT_FLAGS -e JOBSUB_MAX_JOBLOG_HEAD_SIZE"
fi

if [[ "$JOBSUB_MAX_JOBLOG_TAIL_SIZE" ]]; then
    export SUBMIT_FLAGS="$SUBMIT_FLAGS -e JOBSUB_MAX_JOBLOG_TAIL_SIZE"
fi

if [[ "$JOBSUB_DEBUG" ]]; then
    export SUBMIT_FLAGS="$SUBMIT_FLAGS -e JOBSUB_DEBUG"
fi

cp noisy.sh ${GROUP}_noisy.sh
JOBFILE=${GROUP}_noisy.sh
$EXEPATH/jobsub_submit.py $GROUP_SPEC --debug \
       $SERVER_SPEC   $SUBMIT_FLAGS \
            -e SERVER   file://$JOBFILE "here are some args"  2>$0.$GROUP.err
T1=$?
echo T1=$T1
test -s $0.$GROUP.err

T2=$?
echo T2=$T2
cat $0.$GROUP.err


! (( $T1 || $T2 ))
TFINAL=$?
rm $JOBFILE
echo $0 exiting with status $TFINAL
exit $TFINAL

