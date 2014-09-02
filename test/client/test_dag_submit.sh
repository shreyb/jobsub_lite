#!/bin/sh

source ./setup_env.sh

export SERVER=https://${MACH}:8443

$EXEPATH/jobsub_dag_submit --group $GROUP \
--debug $SERVER_SPEC  file://`pwd`/jobsubDagTest/dagTest
T1=$?

echo $0 exiting with status $T1
exit $T1

