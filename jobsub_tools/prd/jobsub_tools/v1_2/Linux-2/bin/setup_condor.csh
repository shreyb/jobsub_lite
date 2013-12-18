#!/bin/csh

setenv PATH ${PATH}:${JOBSUB_TOOLS_DIR}/bin/condor_wrappers
setenv source_me `${JOBSUB_TOOLS_DIR}/bin/setup_condor_csh.py`
unsetenv JOBSUB_UNSUPPORTED_EXPERIMENT

source $source_me
/bin/rm $source_me
unsetenv source_me

if ( "$?SUBMIT_HOST" == "0" ) then
	setenv SUBMIT_HOST gpsn01.fnal.gov
endif

if ( "$JOBSUB_INI_FILE" != "${JOBSUB_TOOLS_DIR}/bin/jobsub.ini" ) then
	echo "using configuration file $JOBSUB_INI_FILE"
endif

setenv PARENT_DIR `dirname $CONDOR_TMP`

if ( ! -d $PARENT_DIR ) then

    mkdir -p $PARENT_DIR
    chgrp ${STORAGE_GROUP} $PARENT_DIR 
    chmod g+w $PARENT_DIR
endif

if ( ! -d $CONDOR_TMP ) then

    mkdir -p $CONDOR_TMP
    chgrp ${STORAGE_GROUP} $CONDOR_TMP 
    chmod g+w $CONDOR_TMP
endif
	
setenv PARENT_DIR `dirname $CONDOR_EXEC`

if ( ! -d $PARENT_DIR ) then

    mkdir -p $PARENT_DIR
    chgrp ${STORAGE_GROUP} $PARENT_DIR
    chmod g+w $PARENT_DIR
   
endif


if ( ! -d $CONDOR_EXEC ) then

    mkdir -p $CONDOR_EXEC
    chgrp ${STORAGE_GROUP} $CONDOR_EXEC
    chmod g+w $CONDOR_EXEC
   
endif

if  $?JOBSUB_UNSUPPORTED_EXPERIMENT  then

	if ! $?GROUP  then
        	echo "warning: no GROUP environment variable set "
	else
		echo "warning: GROUP environtment set to '$GROUP' , dont know what to do"
	endif
        echo "warning: GROUP env variable and your gid="`id -gn` 
        echo "did not identify you as belonging to a supported experiment, setting  GROUP=" $GROUP
        echo "you may submit to the local batch system but your OSG grid"
        echo "access probably will not work unless you have set up a cron job to keep your \\fermilab proxy alive"
        echo "see " 
        echo "https://cdcvs.fnal.gov/redmine/projects/ifront/wiki/Getting_Started_on_GPCF#Set-up-Grid-permissions-and-proxies-before-you-submit-a-job"
	echo "and"
        echo "https://cdcvs.fnal.gov/redmine/projects/ifront/wiki/UsingJobSub#The-probably-will-not-work-error-how-to-make-it-work" 
endif
