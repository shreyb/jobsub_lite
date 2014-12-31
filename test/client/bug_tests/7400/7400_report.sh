#!/bin/sh

here=`pwd`
dir=`basename $here`
outfile=$dir.out
cnt=`grep 'JobsubJobId of first job' $outfile | wc -l` 2>&1
test "$cnt" = "2"
rslt=$?
echo -n "test ${dir}: "
if [ "$rslt" = "0" ] ; then
  echo OK
else
  echo FAILED
fi
exit $rslt
