#!/bin/sh

if [ -e "$JOBSUB_CLIENT_DIR" ];  then
    export EXEPATH=$JOBSUB_CLIENT_DIR
else
    grep 5\. /etc/redhat-release > /dev/null 2>&1
    IS_SL5=$?
    if [ "$IS_SL5" = "0" ] ; then
        . /grid/fermiapp/products/common/etc/setups.sh
        setup python v2_7_3 -f Linux64bit+2.6-2.5
        setup pycurl v7_15_5
    fi
    export X509_CERT_DIR=/etc/grid-security/certificates 
    export X509_USER_CERT=/tmp/x509up_u${UID}
    export X509_USER_KEY=/tmp/x509up_u${UID}

    export EXEPATH=`pwd`"/../../client"
    if [ "$PYTHONPATH" = "" ]; then
            export PYTHONPATH=$EXEPATH
    else
            export PYTHONPATH=$EXEPATH:$PYTHONPATH
    fi
fi
