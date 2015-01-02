#!/bin/sh

source ./setup_env.sh

export SERVER=https://${MACH}:8443

cd jobsubDagTest
$EXEPATH/jobsub_submit_dag  --role Production  $GROUP_SPEC \
--debug $SERVER_SPEC  file://dagTest  --maxConcurrent 3
T1=$?
cd -
echo $0 exiting with status $T1
exit $T1

