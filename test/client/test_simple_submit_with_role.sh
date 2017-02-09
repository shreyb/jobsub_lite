#!/bin/sh

if [ "$1" = "" ]; then
    echo "usage $0 server script_to_submit [script args]"
    echo "test submission to jobsub client/server architecture"
    exit 0
fi
source ./setup_env.sh
export JOB=$1
shift
cp $JOB role_Production.sh



$EXEPATH/jobsub_submit.py --role=Production $GROUP_SPEC  \
        $SERVER_SPEC $SUBMIT_FLAGS \
           -g  -e SERVER  file://role_Production.sh "$@"
T1=$?
echo T1=$T1

$EXEPATH/jobsub_submit.py --role=Production  $GROUP_SPEC  \
        $SERVER_SPEC $SUBMIT_FLAGS \
          -g  -e SERVER  file://role_Production.sh "$@"
T2=$?
echo T2=$T2
#test that bogus roles fail to authenticate
$EXEPATH/jobsub_submit.py --role=bogus_role_that_will_fail  $GROUP_SPEC  \
        $SERVER_SPEC \
          -g  -e SERVER  file://role_Production.sh "$@"
T3=$?
test "$T3" -ne "0"
T3=$?
echo T3=$T3

rm  role_Production.sh

! (( $T1 || $T2 || $T3 ))
TFINAL=$?
echo $0 exiting with status $TFINAL
exit $TFINAL

