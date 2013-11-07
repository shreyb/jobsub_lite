yum -y install libvirt.x86_64
yum -y install policycoreutils-python-2.0.83-19.24.el6.x86_64
yum -y install perl-CPAN.x86_64
cpan Date::Manip
wget http://parrot.cs.wisc.edu//symlink/20131029031510/8/8.0/8.0.4/b887a407c8983474b7f18243d593895e/condor-8.0.4-189770.rhel6.3.x86_64.rpm
rpm -i --nodeps condor-8.0.4-189770.rhel6.3.x86_64.rpm
yum -y install python-setuptools
easy_install pip
pip install distribute --upgrade

yum -y install openssl
yum -y install mod_ssl
yum -y install mod_wsgi
chkconfig --add httpd
chkconfig --level 345 httpd on
#mv /opt/IdleManager/idle_manager.conf /etc/httpd/conf.d/
# set up the certs. not sure this is the right way
scp fcl316.fnal.gov:/etc/grid-security/hostkey.pem /etc/grid-security/
scp fcl316.fnal.gov:/etc/grid-security/hostcert.pem /etc/grid-security/
mkdir /etc/grid-security/certificates
scp -rp fcl316.fnal.gov:/etc/grid-security/certificates /etc/grid-security/
service httpd start
