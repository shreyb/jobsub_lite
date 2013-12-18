#!/bin/sh 
MYGROUP=`id -gn`
MYEXE=jobsub


if [ "$CONDOR_TMP" == "" ]; then
        echo "you must setup jobsub_tools before running this test"
        exit -1
fi


if [ "$CONDOR_TMP" == "" ]; then
	echo "you must setup jobsub_tools before running this test"
	exit -1
fi

if [ ! -e "$CONDOR_EXEC/test_grid_env.sh" ]; then
	cp $JOBSUB_TOOLS_DIR/test/test_grid_env.sh $CONDOR_EXEC
fi

$MYEXE -g --mail_always --OS SL5 $CONDOR_EXEC/test_grid_env.sh 1
$MYEXE -g --mail_always --OS SL5 --nowrapfile $CONDOR_EXEC/test_grid_env.sh 1

$MYEXE -g --mail_always --OS SL5 $CONDOR_EXEC/test_grid_env.sh 1
$MYEXE -g --mail_always --OS SL6 --nowrapfile $CONDOR_EXEC/test_grid_env.sh 1
