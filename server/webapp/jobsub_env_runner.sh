#!/bin/bash
umask 002
DEBUG_JOBSUB=TRUE
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
   source $JOBSUB_UPS_LOCATION >/dev/null 2>&1
else
   echo "ERROR \$JOBSUB_UPS_LOCATION not set in jobsub_api.conf!"
   exit -1
fi

export LOGNAME=$USER
export SUBMIT_HOST=$HOSTNAME


setup jobsub_tools


cd ${COMMAND_PATH_ROOT}/${GROUP}/${USER}/${WORKDIR_ID}
has_exports=`echo $1 |grep 'export_env=' `
RSLT=$?
if [ $RSLT -eq 0 ] ; then
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

echo "${TRANSFER_INPUT_FILES}" | grep "${JOBSUB_COMMAND_FILE_PATH}" > /dev/null 2>&1 
if [ "$?" != "0" ]; then
   export TRANSFER_INPUT_FILES=${JOBSUB_COMMAND_FILE_PATH}${TRANSFER_INPUT_FILES+,$TRANSFER_INPUT_FILES}
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

OWN=" -l +Owner=\\\"$USER\\\" "
#JOBSUB_JOBID="\$(CLUSTER).\$(PROCESS)@$SCHEDD"
export JOBSUB_CMD="jobsub  $OWN $TEC $JSV $JCV $@"

if [ "$DEBUG_JOBSUB" != "" ]; then
   echo "reformulated: ${JOBSUB_CMD} "  >> /tmp/jobsub_env_runner.log
fi

if [ "$JOBSUB_INTERNAL_ACTION" = "SUBMIT" ]; then
    chmod +x ${JOBSUB_COMMAND_FILE_PATH}
fi


RSLT=`$JOBSUB_CMD`
if [ "$DEBUG_JOBSUB" != "" ]; then
   echo "$RSLT "  >> /tmp/jobsub_env_runner.log
fi
#chmod -R g+w $CONDOR_TMP
JID=`echo "$RSLT" | grep 'submitted to cluster' | awk '{print $NF}'`
GOTJID=`echo $JID| grep '[0-9].*'`
WORKED=$?
if [ "$WORKED" = "0" ]; then
  cd ${COMMAND_PATH_ROOT}/${GROUP}/${USER}/
  ln -s $WORKDIR_ID "${JID}0@${SCHEDD}"
  cd -
fi
echo "$RSLT"

if [ "$WORKED" = "0" ]; then
   echo "JobsubJobId of first job: ${JID}0@${SCHEDD}"
   echo "Use job id ${JID}0@${SCHEDD} to retrieve output"
fi
