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
mv /opt/jobsub/jobsub_api.conf /etc/httpd/conf.d/
# link the host keys
mkdir /etc/grid-security/certificates
scp -rp fcl316.fnal.gov:/etc/grid-security/certificates /etc/grid-security/
service httpd start

wget https://www.racf.bnl.gov/Facility/GUMS/mvn/gums/gums-client/1.3.17/gums-client-1.3.17-1.noarch.rpm
rpm -i gums-client-1.3.17-1.noarch.rpm
