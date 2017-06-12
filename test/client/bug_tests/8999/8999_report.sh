#!/bin/sh

#!/bin/sh

SERVER_SAVE=$SERVER
cd ../../
source ./setup_env.sh
cd -

export SERVER=https://${SERVER_SAVE}:8443

here=`pwd`
dir=`basename $here`
outfile=$dir.${GROUP}.out
cnt=`grep 'JobsubJobId of first job' $outfile | wc -l` 2>&1
test "$cnt" = "1"
T1=$?
jobid=`grep 'JobsubJobId of first job' $outfile | awk '{print $5}'`
T2=$?
$EXEPATH/jobsub_fetchlog -G $GROUP $OTHER_TEST_FLAGS --jobsub-server $SERVER --jobid $jobid --dest-dir $GROUP/$jobid >>$outfile 2>&1
T3=$?
grep '+Jobsub_Group' $GROUP/$jobid/*cmd >>$outfile 2>&1
T4=$?
grep '+Jobsub_SubGroup="test"' $GROUP/$jobid/*cmd >>$outfile 2>&1
T5=$?

! (( $T1 || $T2 || $T3 || $T4 || $T5 ))
rslt=$?
echo -n "test ${dir}: "
if [ "$rslt" = "0" ]; then
    echo "OK"
else
    echo "FAILED"
fi
exit $rslt
