#!/bin/sh
#

module=webapp
here=`pwd`
outfile=${here}/pylint.out
docdir=/var/www/html/pydoc/server/webapp/

if [ "$TEST_USER" = "" ]; then
   export TEST_USER=dbox
fi
TEST_BASE=`getent passwd $TEST_USER | cut -d: -f6 `
if [ "${GIT_DIR}" = "" ]; then
   GIT_DIR=${TEST_BASE}/jobsub/server
fi
cd ${GIT_DIR}/${module}   
export PYTHONPATH=${GIT_DIR}:${TEST_BASE}/jobsub/lib/logger:${TEST_BASE}/jobsub/lib/JobsubConfigParser
rm ${docdir}/*.html
for F in `ls *.py`; do 
    P=`echo ${F} | sed 's/\.py//'`
    pydoc -w ${P}
    mv ${P}.html ${docdir}
done
stat=$?
rm *.pyc
cd ${here}
exit $stat
