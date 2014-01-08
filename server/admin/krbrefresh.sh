#!/bin/sh
AUTHORIZED_USER=`grep 'WSGIDaemonProcess jobsub' /etc/httpd/conf.d/jobsub_api.conf | sed s/^.*user=// | sed 's/\ .*$//'`
ME=`whoami`
if [ "$AUTHORIZED_USER" != "$ME" ]; then
    echo "this script must be run as user $AUTHORIZED_USER"
    echo "you are running as $ME"
    echo "exiting...."
    exit 1
fi
export PYTHONPATH=/opt/jobsub/lib/logger/:/opt/jobsub/lib/JobsubConfigParser/:/opt/jobsub/server/webapp
grep  SetEnv /etc/httpd/conf.d/jobsub_api.conf | sed s/SetEnv/export/ | sed 's/\([A-Z]\)\ /\1=/' > /tmp/jobsub_admin_env.sh
source /tmp/jobsub_admin_env.sh
/opt/jobsub/server/webapp/auth.py --refresh-proxies
