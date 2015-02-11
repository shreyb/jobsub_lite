#!/bin/sh
#must be run as root
SPECIAL_PRINCIPAL_LOCATION=$1
if [ "$SPECIAL_PRINCIPAL_LOCATION" = "" ]; then
    echo "usage $0 machine-with-special-principal [jobsub-rpm]"
    echo "installs a jobsub server on a fermicloud machine"
    echo "must be run as root"
    exit 1
    #SPECIAL_PRINCIPAL_LOCATION=rexbatch@some_machine
fi

RPM_LOCATION=$2
if [ "$RPM_LOCATION" = "" ]; then
    RPM_LOCATION=http://web1.fnal.gov/files/jobsub/dev/6/x86_64/jobsub-0.4-0.3.rc3.noarch.rpm
fi

/usr/sbin/groupadd -g 9239 fife
/usr/sbin/groupadd -g 9553 nova
/usr/sbin/useradd -u 8351 dbox
/usr/sbin/useradd -u 47535 -g 9239 rexbatch
/usr/sbin/useradd -u 42417 -g 9553 novapro
echo "rexbatch  ALL=(ALL) NOPASSWD:SETENV: /opt/jobsub/server/webapp/jobsub_priv *" >>  /etc/sudoers
USGR="rexbatch:fife"

rpm -Uvh http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-8.noarch.rpm
yum -y install yum-priorities
rpm -Uvh http://repo.grid.iu.edu/osg/3.2/osg-3.2-el6-release-latest.rpm
JOBSUB_TOOLS_VERSION=$3
if [ "$JOBSUB_TOOLS_VERSION" = "" ]; then
   JOBSUB_TOOLS_VERSION="v1_3_8"
fi

yum -y install upsupdbootstrap-fnal
su products -c ". /fnal/ups/etc/setups.sh; setup ups; setup upd; upd install jobsub_tools ${JOBSUB_TOOLS_VERSION}  -f Linux+2; ups declare -c jobsub_tools ${JOBSUB_TOOLS_VERSION} -f Linux+2; upd install ifdhc v1_4_3; ups declare -c ifdhc v_1_4_3; upd install ups v5_1_2; ups declare -c ups v5_1_2; ups undeclare ups v4_8_0 -f Linux+2"

yum -y install $RPM_LOCATION
yum -y install --enablerepo=osg-development lcmaps-plugins-gums-client
yum -y install --enablerepo=osg-development llrun
cp /etc/lcmaps.db /etc/lcmaps.db.save
cp lcmaps.db /etc/lcmaps.db


mkdir ~rexbatch/.security
scp ${SPECIAL_PRINCIPAL_LOCATION}:.security/*.keytab  ~rexbatch/.security 
chmod -R 700 ~rexbatch/.security
chown -R $USGR  ~rexbatch/.security
LOGDIR=/var/log/jobsub
mkdir -p $LOGDIR
chown $USGR $LOGDIR

JDIRS="tmp creds/certs creds/keytabs creds/krb5cc creds/proxies"
for JD in $JDIRS; do
       DIR=/var/lib/jobsub/$JD
       mkdir -p $DIR
       chown -R $USGR $DIR
       chmod -R 755 $DIR
done


mkdir -p /scratch/uploads/
mkdir -p /scratch/dropbox
touch /scratch/uploads/job.log
chown -R $USGR /scratch/dropbox
chown -R $USGR /scratch/uploads
chmod -R 755 /scratch
chmod -R 755 /scratch/dropbox
chmod -R 775 /scratch/uploads




/usr/sbin/osg-ca-manage setupCA --location root --url osg
/sbin/chkconfig fetch-crl-boot on
/sbin/chkconfig fetch-crl-cron on


INI=/opt/jobsub/server/conf/jobsub.ini
sed s/REPLACE_THIS_WITH_SUBMIT_HOST/$HOSTNAME/ < $INI > $INI.1
sed 's|${LOGNAME}/${LOGNAME}.${GROUP}.proxy|${GROUP}/x509cc_${LOGNAME}|'< $INI.1 > $INI
INI=/etc/httpd/conf.d/jobsub_api.conf
sed 's|/opt/jobsub/server/log|/var/log/jobsub|' < $INI > $INI.1
sed 's/grid /rexbatch /' < $INI.1 > $INI.2
sed 's/condor /fife /' < $INI.2 > $INI

service httpd start
su grid -c '/etc/init.d/condor start'
service condor start
