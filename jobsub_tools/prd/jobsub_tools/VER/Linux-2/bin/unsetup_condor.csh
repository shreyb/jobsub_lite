#!/bin/csh

setenv source_me `${JOBSUB_TOOLS_DIR}/bin/unsetup_condor_sh.py`

source $source_me
if ( "$?REMOVE_JOBSUB_UPS_SOURCE" = "0" ) then
    /bin/rm $source_me
endif

