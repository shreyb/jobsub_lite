#!/bin/bash

if [ "$DEBUG_JOBSUB" != "" ]; then
   cmd="jobsub $@"
   date=`date`
   echo `whoami` >> /tmp/jobsub_env_runner.log
   echo "CWD: `pwd`" >> /tmp/jobsub_env_runner.log
   echo "$date "  >> /tmp/jobsub_env_runner.log
   echo "$cmd "  >> /tmp/jobsub_env_runner.log
fi


source /fnal/ups/etc/setups.sh
#GROUP,USER passed in command line
export USER=$1
shift
export GROUP=$1
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
cmd="jobsub $@"
if [ "$DEBUG_JOBSUB" != "" ]; then
   echo "reformatted: $cmd "  >> /tmp/jobsub_env_runner.log
fi
$cmd

