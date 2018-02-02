#!/bin/sh


AUTHORIZED_USER=`grep 'WSGIDaemonProcess jobsub' /etc/httpd/conf.d/jobsub_api.conf | sed s/^.*user=// | sed 's/\ .*$//'`
thisfile=`basename $0`
pythonfile=`echo $thisfile | sed -e 's/\.sh$/.py/'`

if [ "$1" != "--refresh-pnfs" ] && [ "$1" != "--show-environment" ] ; then

cat <<  USER_DOCUMENTATION
###################################################################
file:  $thisfile
usage: $thisfile [-h] 
                       [--help] 
                       [--refresh-pnfs ]  
                       [--show-environment]

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
export PYTHONPATH=/opt/jobsub/lib/logger/:/opt/jobsub/lib/JobsubConfigParser/:/opt/jobsub/server/webapp:.
grep -i SetEnv /etc/httpd/conf.d/jobsub_api.conf | sed -e 's/[Ss][Ee][Tt][Ee][Nn][Vv]/export/' -e 's/\([A-Z]\)\ /\1=/' -e 's/=[[:space:]]\+/=/'  > /tmp/jobsub_admin_env.sh
source /tmp/jobsub_admin_env.sh
here=`dirname $0`
cd $here
if [ "$1" = "--show-environment" ]; then
    printenv
    exit 0
fi
if [ "$1" = "--refresh-pnfs" ]; then
     /usr/bin/python ./$pythonfile --refresh-pnfs $2
fi
