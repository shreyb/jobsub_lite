#!/bin/bash
source /fnal/ups/etc/setups.sh
setup jobsub_tools
/fnal/ups/prd/jobsub_tools/v1_2k/Linux-2/bin/jobsub "$@"
