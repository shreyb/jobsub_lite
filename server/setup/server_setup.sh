yum -y install libvirt.x86_64
yum -y install policycoreutils-python-2.0.83-19.24.el6.x86_64
yum -y install perl-CPAN.x86_64
cpan Date::Manip

# add grid user
echo grid:x:4287:3302::/home/grid:/bin/bash >> /etc/passwd
mkdir -p /home/grid
chown grid:condor /home/grid
# TODO: have a better way to add voms secrets. Using scp for now
scp -r fermicloud348.fnal.gov:/home/grid/.security /home/grid
chown -R grid:condor /home/grid/.security/

# TODO: add step to install jobsub from ups
# TODO: add step to create the scratch directory with correct permsissions

# this key is needed by condor-python and vo-client.
# TODO: find the right way to get it. Using scp for now
scp fermicloud348.fnal.gov:/etc/pki/rpm-gpg/RPM-GPG-KEY-OSG /etc/pki/rpm-gpg
# TODO: find the right way to get the repo files. Using scp for now
scp -r fermicloud348.fnal.gov:/etc/yum.repos.d /etc

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
wget https://cdcvs.fnal.gov/redmine/attachments/download/14170/jobsub-1.0-0.noarch.rpm
rpm -i jobsub-1.0-0.noarch.rpm

# make sure log file can be written
mkdir -p /opt/jobsub/server/log
chown grid:condor /opt/jobsub/server/log
# set the ini section to the local machine
# TODO: should have a placeholder string instead of fermicloud348.fnal.gov
sed -i 's/fermicloud348.fnal.gov/'"$HOSTNAME"'/g' /opt/jobsub/server/conf/jobsub.ini

# set up apache to start at boot
chmod 700 /home/grid
chkconfig --add httpd
chkconfig --level 345 httpd on
# Certs needed by apache.
mkdir /etc/grid-security/certificates
# TODO: find the right way to get the certs. Using scp for now.
scp -rp fermicloud348.fnal.gov:/etc/grid-security/certificates /etc/grid-security/
service httpd start
