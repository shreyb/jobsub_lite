#scp update_puppet_sl5.sh root@$SERVER:update_puppet_sl5.sh; ssh root@$SERVER '/bin/sh -x ./update_puppet_sl5.sh'
#
wget --no-check-certificate  https://yum.puppetlabs.com/puppetlabs-release-pc1-el-5.noarch.rpm
rpm -Uvh puppetlabs-release-pc1-el-5.noarch.rpm
yum -y --enablerepo puppetlabs-pc1  install puppet-agent
/opt/puppetlabs/bin/puppet  module install puppetlabs-stdlib

