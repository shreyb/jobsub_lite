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
  $GROUP_SPEC  --help
T2=$?
$EXEPATH/jobsub_submit_dag $SERVER_SPEC --help
T3=$?
$EXEPATH/jobsub_submit_dag \
  $SERVER_SPEC \
  $GROUP_SPEC  --help
T4=$?












! (( $T1 || $T2 || $T3 || $T4 ))
T6=$?
echo $0 exiting with status $T6
exit $T6

