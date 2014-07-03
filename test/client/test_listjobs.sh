#!/bin/sh
if [ "$1" = "" ]; then
    echo "usage: $0 servername"
    echo "test that jobs can be listed  on server"
    exit 0
fi
source ./setup_env.sh

JOB=$1

$EXEPATH/jobsub_q.py --group $GROUP $SERVER_SPEC
$EXEPATH/jobsub_q.py --group $GROUP $SERVER_SPEC --jobid $JOB
