#!/bin/sh
source ./setup_env.sh
export SERVER=https://${MACH}:8443
$EXEPATH/jobsub_fetchlog.py $GROUP_SPEC --jobsub-server $SERVER  --list
T1=$?
$EXEPATH/jobsub_fetchlog.py --jobsub-server $SERVER  --list
T2=$?
$EXEPATH/jobsub_fetchlog.py -G GROUP_DOESNT_EXIST --jobsub-server $SERVER  --list
if [ "$?" = "0" ]; then
    T3=1
else
    T3=0
fi
$EXEPATH/jobsub_fetchlog.py --jobsub-server $SERVER  --list-sandboxes
T4=$?

! (( $T1 || $T2 || $T3 || $T4 ))
T5=$?
exit $T5
