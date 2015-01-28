#!/bin/sh
DIR=`dirname $0`
cd $DIR
R1=$?
pwd | grep 'jobsub/test/client' >/dev/null 2>&1
R2=$?
if [ "$R1" != "0" ]  || [ "$R2" != "0" ]; then
    echo "WARNING this program must be run from the test/client "
    echo "directory of a jobsub git repository and nowhere else!  exiting...."
    exit $R1 || $R2
fi
find . -name '*out' -type f  -exec rm -f {} \;
find . -name '*log' -type f  -exec rm -f {} \;
/bin/rm -rf unarchive curl python 
/bin/rm -f  1 
cd -
