#!/bin/bash
#  Comment the line below at the right time
PATH=/usr/local/bin:$PATH
if [ -d "jobsub_vEnv" ];
then
  	echo "jobsub_vEnv exists"
else
	virtualenv --distribute jobsub_vEnv
fi
source jobsub_vEnv/bin/activate
pip install -r requirements.txt

export PATH
