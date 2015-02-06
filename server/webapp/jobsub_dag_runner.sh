#!/bin/bash
umask 002
#DEBUG_JOBSUB=TRUE
WORKDIR=${COMMAND_PATH_ROOT}/${GROUP}/${USER}/${WORKDIR_ID}
WORKDIR_ROOT=${COMMAND_PATH_ROOT}/${GROUP}/${USER}
DEBUG_LOG=${WORKDIR}/jobsub_dag_runner.log
cd ${WORKDIR}

if [ "$DEBUG_JOBSUB" != "" ]; then
   cmd="dagNabbit.py $@"
   date=`date`
   echo `whoami` >> ${DEBUG_LOG}
   echo "CWD: `pwd`" >> ${DEBUG_LOG}
   echo "$date "  >> ${DEBUG_LOG}
   echo "$cmd "  >> ${DEBUG_LOG}
   printenv | sort >> ${DEBUG_LOG}
fi

if [ -e "$JOBSUB_UPS_LOCATION" ]; then
	source $JOBSUB_UPS_LOCATION > /dev/null 2>&1
else
	echo "ERROR \$JOBSUB_UPS_LOCATION not set in jobsub_api.conf!"
	exit -1
fi

export LOGNAME=$USER
export SUBMIT_HOST=$HOSTNAME

setup jobsub_tools

tar xzf ${JOBSUB_PAYLOAD:-payload.tgz}
has_exports=`echo $1 |grep 'export_env=' `
RSLT=$?
if [ $RSLT == 0 ] ; then
	b64=`echo $1 | cut -c14-`
	cmds=`echo $b64 | base64 -d`
	file=`mktemp`
	echo $cmds > $file
	source $file
	shift
        if [ "$DEBUG_JOBSUB" = "" ]; then
          rm $file
        fi
fi

if [ "$ENCRYPT_INPUT_FILES" = "" ]; then
   TEC=""
else
   export TRANSFER_INPUT_FILES=${ENCRYPT_INPUT_FILES}${TRANSFER_INPUT_FILES+,$TRANSFER_INPUT_FILES}
   TEC=" -l encrypt_input_files=$ENCRYPT_INPUT_FILES  -e KRB5CCNAME"
fi

JSV=""
if [ "$JOBSUB_SERVER_VERSION" != "" ]; then
    JSV=" -l +JobsubServerVersion=\\\"$JOBSUB_SERVER_VERSION\\\" "
fi

JCV=""
if [ "$JOBSUB_CLIENT_VERSION" != "" ]; then
    JCV=" -l +JobsubClientVersion=\\\"$JOBSUB_CLIENT_VERSION\\\" "
fi

JOBSUB_JOBID="\\\$(CLUSTER).\\\$(PROCESS)@$SCHEDD"
export JOBSUBPARENTJOBID="\\\$(DAGManJobId)@$SCHEDD"
export JOBSUB_EXPORTS=" -l +JobsubParentJobId=\\\"$JOBSUBPARENTJOBID\\\" -l +JobsubJobId=\\\"$JOBSUB_JOBID\\\" -l +Owner=\\\"$USER\\\" -e JOBSUBPARENTJOBID  $TEC $JSV $JCV "

export JOBSUB_CMD="dagNabbit.py -s -i $@ "

if [ "$DEBUG_JOBSUB" != "" ]; then
   echo "reformulated: $JOBSUB_CMD "  >> ${DEBUG_LOG}
   echo "JOBSUB_EXPORTS: $JOBSUB_EXPORTS "  >> ${DEBUG_LOG}
fi

RSLT=`$JOBSUB_CMD`
if [ "$DEBUG_JOBSUB" != "" ]; then
   echo "$RSLT "  >> ${DEBUG_LOG}
fi
JID=`echo "$RSLT" | grep 'submitted to cluster' | awk '{print $NF}'`
GOTJID=`echo $JID| grep '[0-9].*'`
WORKED=$?
if [ "$WORKED" = "0" ]; then
  cd ${WORKDIR_ROOT}
  ln -s $WORKDIR_ID "${JID}0@${SCHEDD}"
  cd -
fi
echo "$RSLT"

if [ "$WORKED" = "0" ]; then
   echo "JobsubJobId of first job: ${JID}0@${SCHEDD}"
   echo "Use job id ${JID}0@${SCHEDD} to retrieve output"
fi
