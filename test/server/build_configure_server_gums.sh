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
/usr/sbin/useradd -u 8351 dbox
/usr/sbin/useradd -u 47535 -g 9239 rexbatch
# getent passwd | grep pro: | perl -ne '@a=split(":"); $g=$a[0]; $g=~s/pro//; print "/usr/sbin/groupadd -g $a[3] $g\n/usr/bin/useradd -u $a[2] -g $a[3] $a[0]\n";'
/usr/sbin/groupadd -g 9553 nova
/usr/sbin/useradd -u 42417 -g 9553 novapro
/usr/sbin/groupadd -g 5314 auger
/usr/sbin/useradd -u 42418 -g 5314 augerpro
/usr/sbin/groupadd -g 9874 argoneut
/usr/sbin/useradd -u 44544 -g 9874 argoneutpro
/usr/sbin/groupadd -g 9243 ilc
/usr/sbin/useradd -u 46464 -g 9243 ilcpro
/usr/sbin/groupadd -g 9914 mu2e
/usr/sbin/useradd -u 44592 -g 9914 mu2epro
/usr/sbin/groupadd -g 9225 lariat
/usr/sbin/useradd -u 48337 -g 9225 lariatpro
/usr/sbin/groupadd -g 9555 minerva
/usr/sbin/useradd -u 43567 -g 9555 minervapro
/usr/sbin/groupadd -g 9985 darkside
/usr/sbin/useradd -u 47823 -g 9985 darksidepro
/usr/sbin/groupadd -g 6409 mipp
/usr/sbin/useradd -u 42412 -g 6409 mipppro
/usr/sbin/groupadd -g 9954 test
/usr/sbin/useradd -u 42415 -g 9954 testpro
/usr/sbin/groupadd -g 9211 orka
/usr/sbin/useradd -u 47664 -g 9211 orkapro
/usr/sbin/groupadd -g 10043 belle
/usr/sbin/useradd -u 48347 -g 10043 bellepro
/usr/sbin/groupadd -g 5468 minbn
/usr/sbin/useradd -u 42410 -g 5468 minbnpro
/usr/sbin/groupadd -g 1507 dzero
/usr/sbin/useradd -u 42706 -g 1507 dzeropro
/usr/sbin/groupadd -g 9767 fermi
/usr/sbin/useradd -u 43373 -g 9767 fermipro
/usr/sbin/groupadd -g 9960 lbne
/usr/sbin/useradd -u 44539 -g 9960 lbnepro
/usr/sbin/groupadd -g 9990 map
/usr/sbin/useradd -u 44628 -g 9990 mappro
/usr/sbin/groupadd -g 9645 coupp
/usr/sbin/useradd -u 48270 -g 9645 coupppro
/usr/sbin/groupadd -g 5442 cdms
/usr/sbin/useradd -u 42407 -g 5442 cdmspro
/usr/sbin/groupadd -g 9851 icecube
/usr/sbin/useradd -u 44890 -g 9851 icecubepro
/usr/sbin/groupadd -g 5111 minos
/usr/sbin/useradd -u 42411 -g 5111 minospro
/usr/sbin/groupadd -g 9263 lar1
/usr/sbin/useradd -u 48311 -g 9263 lar1pro
/usr/sbin/groupadd -g 9356 genie
/usr/sbin/useradd -u 49563 -g 9356 geniepro
/usr/sbin/groupadd -g 1570 accel
/usr/sbin/useradd -u 42405 -g 1570 accelpro
/usr/sbin/groupadd -g 9950 gm2
/usr/sbin/useradd -u 45651 -g 9950 gm2pro
/usr/sbin/groupadd -g 1540 theo
/usr/sbin/useradd -u 42416 -g 1540 theopro
/usr/sbin/groupadd -g 9937 uboone
/usr/sbin/useradd -u 45225 -g 9937 uboonepro
/usr/sbin/groupadd -g 9511 patri
/usr/sbin/useradd -u 42414 -g 9511 patripro
/usr/sbin/groupadd -g 6269 seaquest
/usr/sbin/useradd -u 47670 -g 6269 seaquestpro


echo "rexbatch  ALL=(ALL) NOPASSWD:SETENV: /opt/jobsub/server/webapp/jobsub_priv *" >>  /etc/sudoers
USGR="rexbatch:fife"

rpm -Uvh http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-8.noarch.rpm
yum -y install yum-priorities
rpm -Uvh http://repo.grid.iu.edu/osg/3.2/osg-3.2-el6-release-latest.rpm
JOBSUB_TOOLS_VERSION=$3
if [ "$JOBSUB_TOOLS_VERSION" = "" ]; then
   JOBSUB_TOOLS_VERSION="v1_3_10"
fi

yum -y install upsupdbootstrap-fnal
su products -c ". /fnal/ups/etc/setups.sh; setup ups; setup upd; upd install jobsub_tools ${JOBSUB_TOOLS_VERSION}  -f Linux+2; ups declare -c jobsub_tools ${JOBSUB_TOOLS_VERSION} -f Linux+2; upd install ifdhc v1_4_3; ups declare -c ifdhc v_1_4_3; upd install ups v5_1_2; ups declare -c ups v5_1_2; ups undeclare ups v4_8_0 -f Linux+2"

yum -y install $RPM_LOCATION
yum -y install --enablerepo=osg-development lcmaps-plugins-gums-client
yum -y install --enablerepo=epel  lcmaps-without-gsi
yum -y install --enablerepo=osg-development llrun

/bin/cp /etc/lcmaps.db /etc/lcmaps.db.save
/bin/cp lcmaps.db /etc/lcmaps.db
mkdir -p /etc/lcmaps
rm -f /etc/lcmaps/lcmaps.db
cd /etc/lcmaps
ln -s ../lcmaps.db .
cd -


mkdir ~rexbatch/.security
scp ${SPECIAL_PRINCIPAL_LOCATION}:~rexbatch/.security/*.keytab  ~rexbatch/.security 
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

USRDIRS=/fife/local/scratch
mkdir -p $USRDIRS
chown -R $USGR $USRDIRS
chmod -R 755 $USRDIRS




/usr/sbin/osg-ca-manage setupCA --location root --url osg
/sbin/chkconfig fetch-crl-boot on
/sbin/chkconfig fetch-crl-cron on


INI=/opt/jobsub/server/conf/jobsub.ini
/bin/cp jobsub.ini $INI
sed s/REPLACE_THIS_WITH_SUBMIT_HOST/$HOSTNAME/ < $INI > $INI.1
sed 's|${LOGNAME}/${LOGNAME}.${GROUP}.proxy|${GROUP}/x509cc_${LOGNAME}|'< $INI.1 > $INI
INI=/etc/httpd/conf.d/jobsub_api.conf
sed 's|/opt/jobsub/server/log|/var/log/jobsub|' < $INI > $INI.1
sed 's/grid /rexbatch /' < $INI.1 > $INI.2
sed 's/condor /fife /' < $INI.2 > $INI

#CERT=/var/lib/jobsub/creds/certs/novapro
#kx509
#sed -n '/-----BEGIN RSA PRIVATE KEY-----/,$p'  /tmp/x509up_u0 > $CERT.key
#sed -n '/-----BEGIN RSA PRIVATE KEY-----/q;p' < /tmp/x509up_u0 > $CERT.cert
#chown $USGR $CERT.key
#chown $USGR $CERT.cert
#chmod 600 $CERT.key
#chmod 600 $CERT.cert
cd /var/lib/jobsub/creds/certs
scp $SPECIAL_PRINCIPAL_LOCATION:/var/lib/jobsub/creds/certs/* .
chown $USGR *
touch /var/lib/condor/spool/history
chown condor /var/lib/condor/spool/history
cat condor_schedds.conf >> /etc/condor/condor_config.local
SPOOL=`condor_config_val SPOOL`
mkdir $SPOOL/1
chown condor $SPOOL/1
mkdir $SPOOL/2
chown condor $SPOOL/2
service httpd start
service condor start
