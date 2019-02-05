#!/bin/sh

function help() {
    echo
    echo "usage:"
    echo 
    echo "$prog somehost.fnal.gov        install jobsub_server on somehost.fnal.gov"
    echo "                                                  use 'create_fermicloud_vm.sh' to create "
    echo "                                                  somehost.fnal.gov on fermicloud if desired "
    echo ""
    echo "$prog --help                   Print this help message and exit"
    echo
    exit 0
}
prog=`basename $0`
if [ $# -ne 1 ]; then
    help
fi
if [ "$1" = "--help" ]; then
    help
fi
#for selinux:
#puppet module install puppet-selinux
#puppet apply -e "class { 'selinux' : mode => 'permissive',}"
export REMOTE_HOST=$1
export REMOTE_SCRIPT=jobsub_host_puppet_apply.sh
puppet module build jobsub_server
scp jobsub_server/pkg/gwms-jobsub_server-0.0.1.tar.gz root@${REMOTE_HOST}:gwms-jobsub_server-0.0.1.tar.gz
echo "for M in \$(puppet module list | grep jobsub_server | awk '{print \$2}'); do" > $REMOTE_SCRIPT
echo "    puppet module uninstall \$M" >> $REMOTE_SCRIPT
echo "done" >> $REMOTE_SCRIPT
echo "puppet module install gwms-jobsub_server-0.0.1.tar.gz" >>$REMOTE_SCRIPT
echo "puppet apply -e \"class { 'jobsub_server' : }\"" >> $REMOTE_SCRIPT
echo "" >> $REMOTE_SCRIPT
scp $REMOTE_SCRIPT root@${REMOTE_HOST}:$REMOTE_SCRIPT
ssh -t root@${REMOTE_HOST} bash $REMOTE_SCRIPT
rm $REMOTE_SCRIPT
