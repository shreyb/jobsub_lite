
#!/bin/sh
if [ "$JOBSUB_TOOLS_DIR" == "" ]; then
	echo "you must first set up jobsub_tools before running this test"
	exit -1
fi

echo "testing a grid job"
$JOBSUB_TOOLS_DIR/test/run_grid_test.sh
echo "testing a local job"
$JOBSUB_TOOLS_DIR/test/run_local_test.sh
echo "testing a dag"
$JOBSUB_TOOLS_DIR/test/run_dag_test.sh


BUSY_TOOL=ifront_q
SUBMIT_NODE=gpsn01.fnal.gov
GRP=`id -gn`
if [ "$GRP" == "e875" ]; then
BUSY_TOOL=minos_q
SUBMIT_NODE=minos25.fnal.gov
fi

echo
echo "---------------------------------------------------------"
echo "condor_q $USER will show the progress of your jobs just "
echo "submitted to $SUBMIT_NODE"
echo "$BUSY_TOOL will show the state of everyones jobs on this node"
echo "---------------------------------------------------------"
echo
echo
