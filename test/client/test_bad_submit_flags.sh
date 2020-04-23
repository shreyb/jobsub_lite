#!/bin/sh

if [ "$1" = "" ]; then
    echo "usage $0 server "
    echo "test submission with two different --group flags, should fail"
    exit 0
fi
source ./setup_env.sh

export SERVER=https://${MACH}:8443

$EXEPATH/jobsub_submit $GROUP_SPEC --group no_such_group --debug \
       $SERVER_SPEC  $SUBMIT_FLAGS \
            -e SERVER   file://simple_worker_script.sh   2>$0.$GROUP.err
res=$?
test $res -ne 0
T1=$?
echo T1=$T1
grep -q 'was given multiple times'  $0.$GROUP.err
T2=$?
echo T2=$T2
! (( $T1 || $T2 ))
TFINAL=$?
echo $0 exiting with status $TFINAL
exit $TFINAL
