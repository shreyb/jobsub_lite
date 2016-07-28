rpm -Uvh https://yum.puppetlabs.com/puppetlabs-release-pc1-el-7.noarch.rpm
yum -y --enablerepo puppetlabs-pc1  install puppet-agent
/opt/puppetlabs/bin/puppet  module install puppetlabs-stdlib

