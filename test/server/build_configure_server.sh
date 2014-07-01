#!/bin/sh
#must be run as root
SPECIAL_PRINCIPAL_LOCATION=$1
if [ "$SPECIAL_PRINCIPAL_LOCATION" = "" ]; then
    echo "usage $0 machine-with-special-principal [jobsub-rpm]"
    echo "installs a jobsub server on a fermicloud machine"
    echo "must be run as root"
    exit 1
fi

RPM_LOCATION=$2
if [ "$RPM_LOCATION" = "" ]; then
    RPM_LOCATION=https://cdcvs.fnal.gov/redmine/attachments/download/14608/jobsub-0.1.1-1.noarch.rpm
fi

rpm -Uvh http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-8.noarch.rpm
yum -y install yum-priorities
rpm -Uvh http://repo.grid.iu.edu/osg/3.2/osg-3.2-el6-release-latest.rpm
echo condor:x:3302:grid >> /etc/group
/usr/sbin/useradd -u 4287 -g 3302 grid

yum -y install upsupdbootstrap-fnal
su products -c ". /fnal/ups/etc/setups.sh; setup ups; setup upd; upd install jobsub_tools v1_3_1_1 -f Linux+2; ups declare -c jobsub_tools v1_3_1_1 -f Linux+2"

yum -y install $RPM_LOCATION


mkdir ~grid/.security
scp ${SPECIAL_PRINCIPAL_LOCATION}:/home/grid/.security/fifegrid.keytab  ~grid/.security 
scp fermicloud326:/home/grid/.security/kadmin_passwd  ~grid/.security 
chmod -R 700 ~grid/.security
chown -R grid:condor ~grid/.security
mkdir -p /opt/jobsub/server/log
chown grid:condor /opt/jobsub/server/log



mkdir -p /scratch/uploads/
mkdir -p /scratch/dropbox
touch /scratch/uploads/job.log
chown -R grid:condor /scratch/dropbox
chown -R grid:condor /scratch/uploads
chmod 755 /scratch
chmod -R 755 /scratch/dropbox
chmod -R 775 /scratch/uploads


CONDOR_CONFIG=/etc/condor/config.d/00personal_condor.config
echo 'CONDOR_IDS = 4287.3302' >> $CONDOR_CONFIG
echo 'QUEUE_SUPER_USERS       = root, condor, grid '>>$CONDOR_CONFIG
echo 'QUEUE_SUPER_USER_MAY_IMPERSONATE = .* '>>$CONDOR_CONFIG
service ypbind stop
/usr/sbin/useradd -u 4716 -g 3302 condor

chown -R grid /var/log/condor
touch /var/lock/subsys/condor
chown -R grid /var/lock/subsys/condor
chown -R grid /var/lock/condor
chown -R grid  /var/run/condor/
chown -R grid /var/lib/condor


/usr/sbin/osg-ca-manage setupCA --location root --url osg
/sbin/chkconfig fetch-crl-boot on
/sbin/chkconfig fetch-crl-cron on


INI=/opt/jobsub/server/conf/jobsub.ini
sed s/REPLACE_THIS_WITH_SUBMIT_HOST/$HOSTNAME/ < $INI > $INI.1
mv $INI.1 $INI
sed 's|${LOGNAME}/${LOGNAME}.${GROUP}.proxy|${GROUP}/x509cc_${LOGNAME}|'< $INI > $INI.1

mv $INI.1 $INI

service httpd start
su grid -c '/etc/init.d/condor start'
service condor start
