#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 servername"
    echo "test that jobsub help is implemented on server"
    exit 0
fi
source ./setup_env.sh


$EXEPATH/jobsub_submit $SERVER_SPEC --help
T1=$?
$EXEPATH/jobsub_submit \
  $SERVER_SPEC \
  $GROUP_SPEC   $SUBMIT_FLAGS --help
T2=$?
$EXEPATH/jobsub_submit_dag $SERVER_SPEC --help
T3=$?
$EXEPATH/jobsub_submit_dag \
  $SERVER_SPEC \
  $GROUP_SPEC   $SUBMIT_FLAGS --help
T4=$?












! (( $T1 || $T2 || $T3 || $T4 ))
TFINAL=$?
echo $0 exiting with status $TFINAL
exit $TFINAL

