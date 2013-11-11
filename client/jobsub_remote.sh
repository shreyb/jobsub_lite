#!/bin/bash

# Find arguments starting with @. Assume it is a file that will be transferred
# TODO: Do we want to upload multiple files?
for arg in "$@"
do
    if [[ "$arg" == @* ]]
    then
        file_upload="-F jobsub_command=$arg"
        echo "File ${arg:1} will be uploaded"
    fi
done

COMMAND=`echo "$@" | base64`
curl -cert /tmp/x509up_u501 -k $file_upload -X POST -F jobsub_args_base64=$COMMAND https://fcint076.fnal.gov:8443/jobsub/experiments/1/jobs/ && echo