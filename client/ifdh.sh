#!/bin/bash

ifdh=$(which ifdh 2>/dev/null)
ups=$(which ups 2>/dev/null)

if [ "$ifdh" = "" ]; then
    if [ "$ups" != "" ]; then
        setup ifdhc ${JOBSUB_IFDH_VERSION}
        ifdh=$(which ifdh 2>/dev/null)
    fi
fi

if [ "$ifdh" = "" ]; then
    SETUP_LIST="/cvmfs/fermilab.opensciencegrid.org/products/common/etc/setups.sh"
    SETUP_LIST="${SETUP_LIST} /grid/fermiapp/products/common/etc/setups.sh "
    SETUP_LIST="${SETUP_LIST} /fnal/ups/etc/setups.sh "
    for SETUP in ${SETUP_LIST}; do
        if [ -e "${SETUP}" ]; then
            source ${SETUP}
            setup ifdhc ${JOBSUB_IFDH_VERSION}
            ifdh=$(which ifdh 2>/dev/null)
            break
        fi
    done
fi

$ifdh $@
