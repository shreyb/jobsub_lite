#!/bin/sh

if [ "$1" = "" ]; then
    echo "usage $0 server script_to_submit [script args]"
    echo "test submission to jobsub client/server architecture"
    exit 0
fi
source ./setup_env.sh

export SERVER=https://${MACH}:8443

$EXEPATH/jobsub_submit.py $GROUP_SPEC --debug \
       $SERVER_SPEC  $SUBMIT_FLAGS \
            -e SERVER   file://"$@"   2>$0.$GROUP.err
T1=$?

test -s $0.$GROUP.err

T2=$?

cat $0.$GROUP.err

$EXEPATH/jobsub_submit.py $GROUP_SPEC \
       $SERVER_SPEC $SUBMIT_FLAGS \
           -g -e SERVER   --verbose file://"$@" 2>$0.$GROUP.err
T3=$?
test -s $0.$GROUP.err

T4=$?

cat $0.$GROUP.err

! (( $T1 || $T2 || $T3  || $T4 ))
TFINAL=$?
echo $0 exiting with status $TFINAL
exit $TFINAL

