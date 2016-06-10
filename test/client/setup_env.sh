#!/bin/sh

if [[ "$GROUP" == ""  && "$JOBSUB_GROUP" = "" ]] ; then
        export GROUP=nova
        export OUTGROUP=nova
fi
export GROUP_SPEC=""
if [ "$GROUP" != "" ]; then
    export GROUP_SPEC=" --group $GROUP"
fi

if [ "$JOBSUB_GROUP" != "" ]; then
    export OUTGROUP=$GROUP
fi

if [ -e "$JOBSUB_CLIENT_DIR" ];  then
    export EXEPATH=$JOBSUB_CLIENT_DIR
else
    grep 5\. /etc/redhat-release > /dev/null 2>&1
    IS_SL5=$?
    if [ "$IS_SL5" = "0" ] ; then
        . /grid/fermiapp/products/common/etc/setups.sh
        setup python v2_7_3 -f Linux64bit+2.6-2.5
        setup pycurl "$PYCURL_VERSION" 
    fi
    export X509_CERT_DIR=/etc/grid-security/certificates 
    #export X509_USER_CERT=/tmp/x509up_u${UID}
    #export X509_USER_KEY=/tmp/x509up_u${UID}

    export EXEPATH=`pwd`"/../../client"
    if [ "$PYTHONPATH" = "" ]; then
            export PYTHONPATH=$EXEPATH
    else
            export PYTHONPATH=$EXEPATH:$PYTHONPATH
    fi
fi
export MACH=$1
shift
export SERVER=https://${MACH}:8443
#to test 7258 uncomment next line
#export SERVER=$MACH 
if [ "$MACH" = "default" ]; then
    export SERVER_SPEC=""
else
    export SERVER_SPEC=" --jobsub-server $SERVER "
fi
if [ "$OTHER_FLAGS" = "" ]; then
    echo -n
else
    export SERVER_SPEC="$SERVER_SPEC $OTHER_FLAGS"
fi
if [ "$POOL" = "" ]; then
    export POOL=$MACH
fi

