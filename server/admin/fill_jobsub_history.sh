#!/bin/sh
export PYTHONPATH=/opt/jobsub/lib/logger/:/opt/jobsub/lib/JobsubConfigParser/:/opt/jobsub/server/webapp
grep  SetEnv /etc/httpd/conf.d/jobsub_api.conf | sed s/SetEnv/export/ | sed 's/\([A-Z]\)\ /\1=/' | sed 's/=[[:space:]]\+/=/' > /tmp/fill_jobsub_history_env.sh
source /tmp/fill_jobsub_history_env.sh
rm /tmp/fill_jobsub_history_env.sh

/opt/jobsub/server/admin/fill_jobsub_history.py $@
exit $?
#TODO
#THERE IS SOME LOGIC BELOW FOR LOADING $SPOOL/history.(older_date) FILES THAT STILL NEEDS TO FIND ITS
#WAY INTO fill_jobsub_history.py   
