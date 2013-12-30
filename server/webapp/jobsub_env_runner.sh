#!/bin/bash
umask 002
#DEBUG_JOBSUB=TRUE
if [ "$DEBUG_JOBSUB" != "" ]; then
   cmd="jobsub $@"
   date=`date`
   echo `whoami` >> /tmp/jobsub_env_runner.log
   echo "CWD: `pwd`" >> /tmp/jobsub_env_runner.log
   echo "$date "  >> /tmp/jobsub_env_runner.log
   echo "$cmd "  >> /tmp/jobsub_env_runner.log
   printenv | sort >> /tmp/jobsub_env_runner.log
fi

if [ -e "$JOBSUB_UPS_LOCATION" ]; then
	source $JOBSUB_UPS_LOCATION
else
	echo "ERROR \$JOBSUB_UPS_LOCATION not set in jobsub_api.conf!"
	exit -1
fi

#GROUP,USER passed in command line
export USER=$1
shift
export GROUP=$1
shift
export WORKDIR_ID=$1
shift
export LOGNAME=$USER
export SUBMIT_HOST=$HOSTNAME
setup jobsub_tools
has_exports=`echo $1 |grep 'export_env=' `
RSLT=$?
if [ $RSLT == 0 ] ; then
	b64=`echo $1 | cut -c14-`
	cmds=`echo $b64 | base64 -d`
	file=`mktemp`
	echo $cmds > $file
	source $file
	shift
fi
export JOBSUB_CMD="jobsub -l "+Owner=\"$USER\"" $@"
#export JOBSUB_CMD="jobsub  $@"
if [ "$DEBUG_JOBSUB" != "" ]; then
   echo "reformulated: $JOBSUB_CMD "  >> /tmp/jobsub_env_runner.log
fi
RSLT=`$JOBSUB_CMD`
if [ "$DEBUG_JOBSUB" != "" ]; then
   echo "$RSLT "  >> /tmp/jobsub_env_runner.log
fi
chmod -R g+w $CONDOR_TMP
JID=`echo $RSLT | awk '{print $NF}'`
GOTJID=`echo $JID| grep '[0-9].*'`
WORKED=$?
if [ "$WORKED" = "0" ]; then
  echo "$JID $USER $GROUP $WORKDIR_ID " >> ${COMMAND_PATH_ROOT}/job.log
fi
echo $RSLT

