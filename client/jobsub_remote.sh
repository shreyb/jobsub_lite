#!/bin/bash

usage()
{
cat << EOF
usage: $0 options

This script submits jobs using the jobsub web service

OPTIONS:
   --help           Show this message
   --jobsub-server  The remote host
   --acct-group     The experiment accounting group
EOF
}

# Gather the arguments to the client
#
# example: fcint076.fnal.gov
JOBSUB_HOST=
# example: minos
ACCOUNTING_GROUP=
while :
do
    case $1 in
        --help)
            usage
            exit 1
            ;;
        --jobsub-server)
            JOBSUB_HOST=$2;
            shift 2;
            ;;
        --acct-group)
            ACCOUNTING_GROUP=$2;
            shift 2;
            ;;
        --)
            shift;
            break;;
        *)  # no more options. Stop while loop
        break
        ;;
    esac
done

if [[ -z $JOBSUB_HOST ]] || [[ -z $ACCOUNTING_GROUP ]]
then
     usage
     exit 1
fi

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

# Encode the jobsub input as base 64
INPUT=`echo "$@"`
BASE64="base64 -w 0"
if [[ `uname` == 'Darwin' ]]; then
    # base64 on OS X does not have -w flag, but does not output newlines
    BASE64="base64"
    # The ca-bundle.crt file can be copied from /etc/pki/tls/certs/ca-bundle.crt on Linux hosts
    CACERT="--cacert ./ca-bundle.crt"
fi
COMMAND=`echo $INPUT | $BASE64`

curl --cert /tmp/x509up_u${UID} $CACERT -H "Accept: application/json" -X POST $file_upload -F jobsub_args_base64=$COMMAND https://$JOBSUB_HOST:8443/jobsub/accountinggroup/$ACCOUNTING_GROUP/jobs/ && echo
