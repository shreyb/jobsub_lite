#!/bin/sh

if [ "$1" = "" ]; then
    echo "usage $0 server  "
    echo "test submission to jobsub client/server architecture"
    exit 0
fi
source ./setup_env.sh

export SERVER=https://${MACH}:8443

SUPPORTED_G="annie argoneut captmnv cdf cdms chips coupp darkside des dune dzero fermilab genie gm2 lar1 lar1nd lariat lbne lsst marsaccel marsgm2 marslbne marsmu2e minerva miniboone minos mu2e numix nova patriot seaquest uboone"
TSUM=0
for GRP in ${SUPPORTED_G}; do
    echo GRP=$GRP
    cp sleep_forever.sh ${GRP}_sleep_forever.sh
    JOBFILE=${GRP}_sleep_forever.sh
    $EXEPATH/jobsub_submit.py -G ${GRP}  --debug \
       $SERVER_SPEC   $SUBMIT_FLAGS \
            -e SERVER   file://$JOBFILE "here are some args"  2>$0.${GRP}.err
    T1=$?
    echo T1=$T1
    $EXEPATH/jobsub_submit_dag   -G ${GRP} \
        --debug $SERVER_SPEC  file://dagSleep  

    T2=$?
    echo T2=$T2

    ! (( $T1 || $T2 || $TSUM ))
    TSUM=$?
    echo group ${GRP} TSUM=${TSUM}
    rm $JOBFILE
done
echo $0 exiting with status $TSUM
exit $TSUM

