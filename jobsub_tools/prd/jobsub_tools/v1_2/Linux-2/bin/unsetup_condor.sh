#!/bin/sh

export source_me=`${JOBSUB_TOOLS_DIR}/bin/unsetup_condor_sh.py`

source $source_me
if [ "$REMOVE_JOBSUB_UPS_SOURCE" = "" ] 
then
        /bin/rm $source_me
fi

unset source_me
