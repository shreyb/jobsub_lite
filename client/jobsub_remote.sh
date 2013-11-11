#!/bin/bash
INPUT=`echo "$@"`

BASE64="base64 -w 0"
if [[ `uname` == 'Darwin' ]]; then
    BASE64="base64"
fi
COMMAND=`echo $INPUT | $BASE64`

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

curl -cert /tmp/x509up_u${UID} -k -X POST $file_upload -F jobsub_args_base64=$COMMAND https://fermicloud326.fnal.gov:8443/jobsub/experiments/1/jobs/ && echo