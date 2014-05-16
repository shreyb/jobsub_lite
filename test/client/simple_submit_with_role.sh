#!/bin/sh

if [ "$1" = "" ]; then
    echo "usage $0 server script_to_submit [script args]"
    echo "test submission to jobsub client/server architecture"
    exit 0
fi
source ./setup_env.sh
export JOB=$1
shift
cp $JOB role_Analysis.sh
cp $JOB role_Production.sh



$EXEPATH/jobsub_submit.py --role=Production --group $GROUP  \
        $SERVER_SPEC \
           -g  -e SERVER  file://role_Production.sh "$@"

$EXEPATH/jobsub_submit.py --role=Analysis  --group $GROUP  \
        $SERVER_SPEC \
          -g  -e SERVER  file://role_Analysis.sh "$@"

rm role_Analysis.sh role_Production.sh
