#!/bin/bash
source /fnal/ups/etc/setups.sh
setup jobsub_tools
jobsub "$@"
