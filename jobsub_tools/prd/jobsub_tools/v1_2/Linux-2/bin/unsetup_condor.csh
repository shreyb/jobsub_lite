#!/bin/csh

setenv source_me `${JOBSUB_TOOLS_DIR}/bin/unsetup_condor_sh.py`

source $source_me
/bin/rm $source_me
