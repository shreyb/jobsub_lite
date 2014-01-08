#!/bin/sh

export PYTHONPATH=/opt/jobsub/lib/logger/:/opt/jobsub/lib/JobsubConfigParser/:/opt/jobsub/server/webapp
grep  SetEnv /etc/httpd/conf.d/jobsub_api.conf | sed s/SetEnv/export/ | sed 's/\([A-Z]\)\ /\1=/' > /tmp/jobsub_admin_env.sh
source /tmp/jobsub_admin_env.sh
/opt/jobsub/server/webapp/auth.py --refresh-proxies
