#!/bin/bash
#umask 002
WORKDIR=${COMMAND_PATH_ROOT}/${GROUP}/${USER}/${WORKDIR_ID}
WORKDIR_ROOT=${COMMAND_PATH_ROOT}/${GROUP}/${USER}
DEBUG_LOG=${WORKDIR}/jobsub_env_runner.log
export JOBSUB_INI_FILE=/opt/jobsub/server/conf/jobsub.ini

if [ -e "$JOBSUB_UPS_LOCATION" ]; then
   source $JOBSUB_UPS_LOCATION >/dev/null 2>&1
else
   echo "ERROR \$JOBSUB_UPS_LOCATION not set in jobsub_api.conf!"
   exit -1
fi

export LOGNAME=$USER
export SUBMIT_HOST=$HOSTNAME




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
        else
          echo "source file:$file" >> $DEBUG_LOG
        fi
fi

if [ "$USE_UPS_JOBSUB_TOOLS" = "" ]; then
    export CONDOR_TMP=${WORKDIR}
    export PYTHONPATH=/opt/jobsub/lib/groupsettings:/opt/jobsub/lib/JobsubConfigParser:/opt/jobsub/lib/logger:/opt/jobsub/lib:$PYTHONPATH
    export PATH=/opt/jobsub/server/tools:$PATH
else
     setup jobsub_tools
fi 

if [ "$DEBUG_JOBSUB" != "" ]; then
   cmd="jobsub $@"
   date=`date`
   echo `whoami` >> $DEBUG_LOG
   echo "CWD: `pwd`" >> $DEBUG_LOG
   echo "$date "  >> $DEBUG_LOG
   echo "$cmd "  >> $DEBUG_LOG
   printenv | sort >> $DEBUG_LOG
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

JCDN=""
if [ "$JOBSUB_CLIENT_DN" != "" ]; then
    export JOBSUB_CLIENT_DN=`echo $JOBSUB_CLIENT_DN | sed "s/'//"`
    JCDN=" -l +JobsubClientDN=\\\"'"$JOBSUB_CLIENT_DN"'\\\" "
fi

JCIA=""
if [ "$JOBSUB_CLIENT_IP_ADDRESS" != "" ]; then
    JCIA=" -l +JobsubClientIpAddress=\\\"$JOBSUB_CLIENT_IP_ADDRESS\\\" "
fi

OWN=" -l +Owner=\\\"$USER\\\" -l +Jobsub_Submit_Host=\\\"$SUBMIT_HOST\\\" -l +Jobsub_Submit_Dir=\\\"$WORKDIR\\\" "
JCKP=" -l +JobsubClientKerberosPrincipal=\\\"$JOBSUB_CLIENT_KRB5_PRINCIPAL\\\" "

#JOBSUB_JOBID="\$(CLUSTER).\$(PROCESS)@$SCHEDD"
export JOBSUB_CMD="jobsub  --schedd $SCHEDD $JCDN $JCIA $OWN $TEC $JSV $JCV $JCKP $@"

if [ "$DEBUG_JOBSUB" != "" ]; then
   echo "reformulated: $JOBSUB_CMD "  >> $DEBUG_LOG
fi

if [ "$JOBSUB_INTERNAL_ACTION" = "SUBMIT" ]; then
    cd ${WORKDIR}
fi


RSLT=`$JOBSUB_CMD`
if [ "$DEBUG_JOBSUB" != "" ]; then
   echo "$RSLT "  >> $DEBUG_LOG
fi
#chmod -R g+w $CONDOR_TMP
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

echo "$@" | grep '\-\-help' > /dev/null 2>&1
FOUND_HELP_FLAG=$?

echo "$@" | grep '\-\-version' > /dev/null 2>&1
FOUND_VERSION_FLAG=$?

if [ "$FOUND_HELP_FLAG" = "0" ];then
   exit $FOUND_HELP_FLAG
elif [ "$FOUND_VERSION_FLAG" = "0" ];then
   exit $FOUND_VERSION_FLAG
else
   exit $WORKED
fi
