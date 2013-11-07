#!/bin/bash

COMMAND=`echo "$@" | base64`
curl -cert /tmp/x509up_u501 -k -X POST -d -jobsub_args_base64=$COMMAND https://fcint076.fnal.gov:8443/jobsub/experiments/1/jobs/ && echo