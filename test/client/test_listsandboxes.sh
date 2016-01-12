#!/bin/sh
source ./setup_env.sh
export SERVER=https://${MACH}:8443
$EXEPATH/jobsub_fetchlog.py $GROUP_SPEC --jobsub-server $SERVER  --list
T1=$?
echo T1=$T1
if [ "$SKIP_PRODUCTION_TEST" = "" ]; then
    $EXEPATH/jobsub_fetchlog.py $GROUP_SPEC --role Production --jobsub-server $SERVER  --list
    T2=$?
else
    T2=0
fi
echo T2=$T2
$EXEPATH/jobsub_fetchlog.py -G GROUP_DOESNT_EXIST --jobsub-server $SERVER  --list
if [ "$?" = "0" ]; then
    T3=1
else
    T3=0
fi
echo T3=$T3
$EXEPATH/jobsub_fetchlog.py $GROUP_SPEC --user dbox --jobsub-server $SERVER  --list-sandboxes
T4=$?
echo T4=$T4

! (( $T1 || $T2 || $T3 || $T4 ))
T5=$?
exit $T5
