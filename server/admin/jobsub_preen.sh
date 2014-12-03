#!/bin/sh
export PYTHONPATH=/opt/jobsub/lib/logger/:/opt/jobsub/lib/JobsubConfigParser/:/opt/jobsub/server/webapp
grep  SetEnv /etc/httpd/conf.d/jobsub_api.conf | sed s/SetEnv/export/ | sed 's/\([A-Z]\)\ /\1=/' | sed 's/=[[:space:]]\+/=/' > /tmp/jobsub_preen_env.sh
source /tmp/jobsub_preen_env.sh
rm /tmp/jobsub_preen_env.sh

/opt/jobsub/server/admin/jobsub_preen.py $@

