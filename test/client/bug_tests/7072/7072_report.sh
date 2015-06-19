#!/bin/sh

here=`pwd`
dir=`basename $here`
outfile=$dir.$GROUP.out
cnt=`grep 'JobsubJobId of first job' $outfile | wc -l` 2>&1
test "$cnt" = "1"
rslt=$?
echo -n "test $dir: "
if [ "$rslt" = "0" ] ; then
  echo submission was OK
  jobid=`grep 'JobsubJobId of first job' $outfile | awk '{print $5}'`
  echo "to see if feature successful: jobsub_fetchlog \$SERVER --jobid $jobid "
else
  echo FAILED
fi
exit $rslt
