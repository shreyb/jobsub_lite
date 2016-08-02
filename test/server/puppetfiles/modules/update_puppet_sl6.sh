#scp update_puppet_sl6.sh root@$SERVER:update_puppet_sl6.sh; ssh root@$SERVER '/bin/sh -x ./update_puppet_sl6.sh
rpm -Uvh https://yum.puppetlabs.com/puppetlabs-release-pc1-el-6.noarch.rpm
yum -y --enablerepo puppetlabs-pc1  install puppet-agent
/opt/puppetlabs/bin/puppet  module install puppetlabs-stdlib

