#!/bin/sh
CMDFILE=$1
CONDOR_TMP=`dirname $CMDFILE`
PYTHONPATH=$JOBSUB_TOOLS_DIR/pylib/DAGParser/
OUTFILE=$CONDOR_TMP/summary.out
DAGLOGFILE=`ls $CONDOR_TMP/*dag.nodes.log`
DAGPARENTLOGFILE=`ls $CONDOR_TMP/*dag.dagman.log`
MAILTO=`grep notify_user $CMDFILE | sed -e 's/notify_user = //'`
export CMDFILE PYTHONPATH CONDOR_TMP OUTFILE DAGLOGFILE DAGPARENTLOGFILE MAILTO
JOBSUBPARENTJOBID=`grep ^000 ${DAGPARENTLOGFILE} | sed -e 's/000 (//' | sed -e 's/\.00.*/\.0\@/'`
HOST=`hostname`
JOBSUBPARENTJOBID="${JOBSUBPARENTJOBID}${HOST}"
export JOBSUBPARENTJOBID
SUBJECT="Job $JOBSUBPARENTJOBID Status Summary"
export SUBJECT
/bin/echo ''> $OUTFILE
/bin/echo "$SUBJECT" >> $OUTFILE
/bin/echo "--------------------------" >> $OUTFILE
/bin/echo '' >> $OUTFILE
python $JOBSUB_TOOLS_DIR/pylib/DAGParser/PrintSummary.py $DAGLOGFILE >> $OUTFILE 2>&1

mail -s "$SUBJECT" $MAILTO < $OUTFILE
exit 0
