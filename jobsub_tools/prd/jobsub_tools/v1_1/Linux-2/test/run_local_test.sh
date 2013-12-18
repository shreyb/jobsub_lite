#!/bin/sh 

MYGROUP=`id -gn`
MYEXE=jobsub


if [ "$CONDOR_TMP" == "" ]; then
	echo "you must setup jobsub_tools before running this test"
	exit -1
fi

if [ ! -e "$CONDOR_EXEC/test_local_env.sh" ]; then
	cp $JOBSUB_TOOLS_DIR/test/test_local_env.sh $CONDOR_EXEC
fi

$MYEXE -g $CONDOR_EXEC/test_local_env.sh
