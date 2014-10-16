#!/bin/sh

source ./setup_env.sh

export SERVER=https://${MACH}:8443

cd jobsubDagTest
$EXEPATH/jobsub_submit_dag --group $GROUP \
--debug $SERVER_SPEC  file://dagTest
T1=$?
cd -
echo $0 exiting with status $T1
exit $T1

