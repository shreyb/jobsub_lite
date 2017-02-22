#!/bin/bash
this_script=$0
here=$(pwd)
bd=$(dirname $here)
while [ "$(basename $bd)" != "jobsub" ]; do
    bd=$(dirname $bd)
done
PYTHONPATH="$bd"/server/webapp:"$bd"/lib/JobsubConfigParser:"$bd"/lib/logger:$here
export PYTHONPATH
export JOBSUB_LOG_DIR=/tmp
export JOBSUB_INI_FILE=/opt/jobsub/server/conf/jobsub.ini
export JOBSUB_SERVER=$HOSTNAME

