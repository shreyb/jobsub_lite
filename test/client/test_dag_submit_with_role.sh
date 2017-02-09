#!/bin/sh

source ./setup_env.sh

export SERVER=https://${MACH}:8443

cd jobsubDagTest
$EXEPATH/jobsub_submit_dag $SUBMIT_FLAGS --role Production  $GROUP_SPEC \
--debug $SERVER_SPEC  file://dagTest  --maxConcurrent 3
T1=$?
cd -
TFINAL=$T1
echo $0 exiting with status $TFINAL
exit $TFINAL

