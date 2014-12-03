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



$EXEPATH/jobsub_submit.py --role=Production $GROUP_SPEC  \
        $SERVER_SPEC $SUBMIT_FLAGS \
           -g  -e SERVER  file://role_Production.sh "$@"
T1=$?
$EXEPATH/jobsub_submit.py --role=Analysis  $GROUP_SPEC  \
        $SERVER_SPEC $SUBMIT_FLAGS \
          -g  -e SERVER  file://role_Analysis.sh "$@"
T2=$?
rm role_Analysis.sh role_Production.sh

! (( $T1 || $T2 ))
T3=$?
echo $0 exiting with status $T3
exit $T3

