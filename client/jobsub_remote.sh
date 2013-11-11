#!/bin/bash
INPUT=`echo "$@"`
UID=`id -u`
COMMAND=`echo $INPUT | base64 -w 0`
curl -cert /tmp/x509up_u${UID}.p12 -k -X POST -d -jobsub_args_base64=$COMMAND https://fermicloud326.fnal.gov:8443/jobsub/experiments/1/jobs/ && echo
