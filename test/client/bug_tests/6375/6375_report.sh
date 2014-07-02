#!/bin/sh

here=`pwd`
dir=`basename $here`
outfile=$dir.out
grep 'authorization has failed' $outfile > /dev/null 2>&1
rslt=$?
echo -n "test $dir: "
if [ "$rslt" = "0" ] ; then
  echo OK
else
  echo FAILED
fi
exit $rslt
