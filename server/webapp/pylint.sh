#!/bin/sh
#

module=webapp
here=`pwd`
outfile=${here}/pylint.out

if [ "$TEST_USER" = "" ]; then
   export TEST_USER=dbox
fi
TEST_BASE=`getent passwd $TEST_USER | cut -d: -f6 `
if [ "${GIT_DIR}" = "" ]; then
   GIT_DIR=${TEST_BASE}/jobsub/server
fi
cd ${GIT_DIR}/${module}   
export PYTHONPATH=${GIT_DIR}:${TEST_BASE}/jobsub/lib/logger:${TEST_BASE}/jobsub/lib/JobsubConfigParser
/usr/bin/pylint --include-naming-hint=y -f parseable  *.py  > ${outfile}
cat ${outfile}
grep 'E0001' ${outfile} > /dev/null 2>&1
stat=$?
cd ${here}
if [ "$stat" = "0" ] ; then
   exit 1
else
   exit 0
fi
