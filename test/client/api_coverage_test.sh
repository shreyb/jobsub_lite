#!/bin/bash
if [ "$1" = "" ]; then
    echo "usage $0 server  "
    echo "test a list of api endpoints against a jobsub server"
    exit 0
fi
source ./setup_env.sh

export JOBSUB_SERVER=https://${MACH}:8443


LLL="========================================================================="
mkdir -p api_coverage_output
for URL in $(cat api_coverage_list); do 
    eval "ENDPT=$URL"
    OUT="api_coverage_output/$(echo $ENDPT | sed -e 's/\//_/g' -e 's/\@/_/' -e 's/\://').out"
    CMD="$EXEPATH/jobsub_probe_url -G $GROUP  --jobsub-server $JOBSUB_SERVER "
    CMD="$CMD --endpoint $ENDPT  --action GET --debug "
    echo $LLL
    echo "testing GET $JOBSUB_SERVER""$ENDPT " 
    $CMD > $OUT 2>&1
    STAT=$?
    echo "exit code $STAT"
    echo $LLL
done


