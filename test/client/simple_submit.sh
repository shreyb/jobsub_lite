#!/bin/sh

if [ "$1" = "" ]; then
    echo "usage $0 server script_to_submit [script args]"
    echo "test submission to jobsub client/server architecture"
    exit 0
fi
grep 5\. /etc/redhat-release > /dev/null 2>&1
IS_SL5=$?
if [ "$IS_SL5" = "0" ] ; then
. /grid/fermiapp/products/common/etc/setups.sh
setup python v2_7_3 -f Linux64bit+2.6-2.5
setup pycurl v7_15_5
fi
export MACH=$1
shift
export X509_CERT_DIR=/etc/grid-security/certificates 
export X509_USER_CERT=/tmp/x509up_u8531
export X509_USER_KEY=/tmp/x509up_u8531

export SERVER=https://${MACH}:8443
export PYTHONPATH="../../client"

$PYTHONPATH/jobsub_submit.py --group nova --debug \
       --jobsub-server $SERVER \
            -e SERVER --nowrapfile   file://"$@"

$PYTHONPATH/jobsub_submit.py --group nova \
       --jobsub-server $SERVER \
           -g -e SERVER --nowrapfile   file://"$@"
