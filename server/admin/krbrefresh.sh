#!/bin/sh


AUTHORIZED_USER=`grep 'WSGIDaemonProcess jobsub' /etc/httpd/conf.d/jobsub_api.conf | sed s/^.*user=// | sed 's/\ .*$//'`

if [ "$1" != "--refresh-proxies" ] ; then

cat <<  USER_DOCUMENTATION
###################################################################
file:krbrefresh.sh
usage: krbrefresh.sh [ -h ] 
                     [--help] 
                     [--refresh-proxies ]  [age_in_seconds]

it must be run as user $AUTHORIZED_USER who has the ability to refresh user 
kerberos principals and voms-proxies in \$JOBSUB_CREDENTIALS_DIR

This script refreshes the kerberos proxies of any user in the queue 
that has a kerberos principal older than [age_in_seconds].  If no
[age_in_seconds] argument is given, the default of 3600 seconds is used.

This script logs its actions to file $JOBSUB_LOG_DIR/krbrefresh.log
JOBSUB_LOG_DIR is set in the webservers jobsub_api.conf file
##################################################################
USER_DOCUMENTATION
exit 0
fi

ME=`whoami`
if [ "$AUTHORIZED_USER" != "$ME" ]; then
    echo "this script must be run as user $AUTHORIZED_USER"
    echo "you are running as $ME"
    echo "exiting...."
    exit 1
fi
#export PYTHONPATH=/opt/jobsub/lib/logger/:/opt/jobsub/lib/JobsubConfigParser/:/opt/jobsub/server/webapp
grep -i SetEnv /etc/httpd/conf.d/jobsub_api.conf | sed -e 's/[Ss][Ee][Tt][Ee][Nn][Vv]/export/' -e 's/\([A-Z]\)\ /\1=/' -e 's/=[[:space:]]\+/=/'  > /tmp/jobsub_admin_env.sh  > /tmp/jobsub_admin_env.sh
grep python-path /opt/jobsub/server/conf/jobsub_api.conf | sed -e 's/.*python-path/export PYTHONPATH/' -e 's/=[[:space:]]\+//'>>/tmp/jobsub_admin_env.sh
source /tmp/jobsub_admin_env.sh

if [ "$1" = "--refresh-proxies" ]; then
     /usr/bin/python /opt/jobsub/server/webapp/auth.py --refresh-proxies $2
fi
