#!/bin/bash -x
if [ "$JOBSUB_SETUP_SOURCED" = "" ]; then
    export JOBSUB_SETUP_SOURCED=1
    for F in /cvmfs/fermilab.opensciencegrid.org/products/common/setups /grid/fermiapp/products/common/etc/setups /fnal/ups/etc/setups; do
        if [ -e "$F" ]; then
            source $F
            break
        fi
    done
    PYFLAVOR=$(eval $(which pyflavor))
    if [ "$PYFLAVOR" = "" ]; then
        PYFLAVOR=../../client/pyflavor
    fi
    if [ ! test -f "$PYFLAVOR" ]; then
        PYFLAVOR=python2.6
    fi
    setup python_future_six_request -q $PYFLAVOR
    setup cigetcert
    setup kx509
    export KRB5CCNAME=`ls -lart /tmp/krb5cc_${UID}* | tail -1 | awk '{print $9}'`
    kx509
    export EXPERIMENT=$GROUP
    setup ifdhc
fi
