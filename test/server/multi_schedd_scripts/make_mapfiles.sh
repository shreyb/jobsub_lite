#!/bin/bash
SCHEDD_LIST=""
JOBSUB_SERVER_LIST=""
GLOBAL_CONFIG="00_cluster_hostnames.config  01_global.config" 
SCHEDD_CONFIG=03_standalone_schedd.config
COLLECTOR_CONFIG=04_collector_negotiator_schedd.config
SERVER_CONFIG=02_jobsub_server.config

HOSTS=""
#/bin/rm condor_mapfile
#touch condor_mapfile
echo GSI '"'/DC=org/DC=cilogon/C=US/O=Fermi National Accelerator Laboratory/OU=People/CN=Dennis Box/CN=UID:dbox'"' dbox > condor_mapfile
for L in $(grep fermicloud $1); do
    H=$(echo $L | sed s/^.*=//g)
    HOSTS="$HOSTS $H"
    echo GSI '"'/DC=org/DC=opensciencegrid/O=Open Science Grid/OU=Services/CN=$H'"' rexbatch >> condor_mapfile
done
echo 'GSI (.*) anonymous' >> condor_mapfile
echo 'FS (.*) \1' >> condor_mapfile

sed -e 's/=/=\"/' -e 's/$/\"/' -e 's/(//g' -e 's/)//g' -e 's/,/ /g'   $1 > hostnames.sh
for H in $HOSTS; do
    ssh root@$H 'mkdir -p /etc/condor/certs/'
    scp condor_mapfile root@$H:/etc/condor/certs/condor_mapfile
    scp iptables root@$H:/etc/sysconfig/iptables
done
source hostnames.sh

for H in $CONDOR_HOST; do
    ssh root@$H '/bin/rm -f /etc/condor/config.d/99.local.config'
    for F in $GLOBAL_CONFIG; do
        scp $F root@$H:/etc/condor/config.d/$F
    done
done

for H in $SCHEDD_LIST $COLLECTOR_HOST; do
   scp $SCHEDD_CONFIG root@$H:/etc/condor/config.d
   ssh root@$H service httpd stop
   ssh root@$H service jenkins stop
done

#for H in $COLLECTOR_HOST; do
#scp $SCHEDD_CONFIG root@$COLLECTOR_HOST:/etc/condor/config.d

for H in $JOBSUB_SERVER_LIST; do
   scp $SERVER_CONFIG root@$H:/etc/condor/config.d
   scp local_jobsub_source.sh root@$H:local_jobsub_source.sh
   ssh root@$H ./local_jobsub_source.sh
   ssh root@$H service httpd restart
done

scp $COLLECTOR_CONFIG root@$COLLECTOR_HOST:/etc/condor/config.d

for H in $CONDOR_HOST; do
    ssh root@$H 'service iptables restart'
    ssh root@$H 'service condor restart'
done
