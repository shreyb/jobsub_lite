# Update the yum repos
rpm -Uvh http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-8.noarch.rpm
yum -y install yum-priorities
rpm -Uvh http://repo.grid.iu.edu/osg/3.2/osg-3.2-el6-release-latest.rpm

# Set up the CA
yum -y install osg-ca-scripts
/usr/sbin/osg-ca-manage setupCA --location root --url osg
/sbin/service osg-update-certs-cron  start
yum -y install fetch-crl
/sbin/chkconfig fetch-crl-boot on
/sbin/chkconfig fetch-crl-cron on

# add grid user
/usr/sbin/useradd -u 4287 -g 3302 grid

# TODO: have a better way to add voms secrets. Using scp for now
scp -r fermicloud075.fnal.gov:/home/grid/.security /home/grid
chown -R grid:condor /home/grid/.security/

# Install jobsub from ups
yum -y install upsupdbootstrap-fnal
su products -c ". /fnal/ups/etc/setups.sh; setup ups; setup upd; upd install jobsub_tools v1_2n -f Linux+2; ups declare -c jobsub_tools v1_2n -f Linux+2"

# Get the dependencies
yum -y install openssl
yum -y install mod_ssl
yum -y install mod_wsgi
yum -y install condor-python
yum -y install krb5-fermi-getcert
yum -y install python-cherrypy
yum -y install vo-client
yum -y install voms-clients

# get and install the jobsub webapp rpm
# pull rpm from redmine and install
# TODO: find the right way to store the jobsub rpm. Probably should be added to yum repo
wget https://cdcvs.fnal.gov/redmine/attachments/download/14308/jobsub-0.1-3.noarch.rpm
rpm -ivh jobsub-0.1-3.noarch.rpm
# make sure log file can be written
mkdir -p /opt/jobsub/server/log
chown grid:condor /opt/jobsub/server/log
# Create the scratch directory with correct permsissions
# rpm spec file looks like it creates these but it doesnt
mkdir -p /scratch/data
mkdir -p /scratch/proxies
mkdir -p /scratch/app
mkdir -p /scratch/uploads/
mkdir -p /scratch/dropbox/
touch /scratch/uploads/job.log
chown -R grid:condor /scratch
chmod -R 777 /scratch

# set the ini section to the local machine
sed -i 's/REPLACE_THIS_WITH_SUBMIT_HOST/'"$HOSTNAME"'/g' /opt/jobsub/server/conf/jobsub.ini

# set up apache to start at boot
chmod 700 /home/grid
chkconfig --add httpd
chkconfig --level 345 httpd on

service httpd start
service condor start
