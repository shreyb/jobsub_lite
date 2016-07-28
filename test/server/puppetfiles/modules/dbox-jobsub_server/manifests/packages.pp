class jobsub_server::packages (String $ifdhc_version = $jobsub_server::vars::ifdhc_version, 
                               String $jobsub_tools_version = $jobsub_server::vars::jobsub_tools_version,
                               String $ups_version = $jobsub_server::vars::ups_version,
                               String $ups_flavor = $jobsub_server::vars::ups_flavor ) {
    yumrepo { 'jobsub':
      baseurl  => 'http://web1.fnal.gov/files/jobsub/dev/6/x86_64/',
      descr    => 'Jobsub',
      enabled  => 1,
      gpgcheck => 0,
    }

    package { 'epel-release-6':
      ensure   => 'installed',
      provider => 'rpm',
      source   => 'https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm',
    }

    package { 'osg-release-3.3-5.osg33.el6.noarch':
      ensure   => 'installed',
      provider => 'rpm',
      source   => 'https://repo.grid.iu.edu/osg/3.3/osg-3.3-el6-release-latest.rpm',
      notify   => Exec['yum-clean-all'],
    }

    exec { 'yum-clean-all':
      command => '/bin/echo yum clean all',
    }

    package { 'fermilab-util_kx509.noarch' :
      ensure => 'present',
    }


    package {'git': ensure => present}
    package { 'httpd': ensure => present}
    package { 'upsupdbootstrap-fnal': ensure => present }

    package { 'llrun':
      ensure          => present,
      install_options => '--enablerepo=osg-development',
    }

    package { 'lcmaps-plugins-gums-client':
      ensure          => present,
      install_options => '--enablerepo=osg-development',
    }

    package { 'lcmaps-without-gsi':
      ensure          => present,
      install_options => '--enablerepo=epel',
    }

    package { 'myproxy':
      ensure          => present,
      install_options => '--enablerepo=osg',
    }

      
    package { 'uberftp':
      ensure          => present,
      install_options => '--enablerepo=osg',
    }

    package { 'globus-ftp-client':
      ensure          => present,
      install_options => '--enablerepo=osg',
    }


    package { 'condor':
      ensure          => present,
      install_options => '--enablerepo=osg',
    }

    package { 'jobsub':
      ensure          => $jobsub_server::vars::jobsub_server_version,
      install_options => '--enablerepo=jobsub',
      require => Package['voms-clients-cpp'],
    }

    package { 'voms-clients-cpp':
      install_options => '--enablerepo=osg-development',
    }

    package { 'osg-ca-scripts':
      ensure          => present,
      install_options => '--enablerepo=osg',
    }
  
    #install these ups products and make them current
    jobsub_server::ups::product {
      'ups'          : version => $ups_version, qualifier => "-f ${ups_flavor}";
      'jobsub_tools' : version => $jobsub_tools_version, qualifier => "-f Linux+2" ;
      'ifdhc'        : version => $ifdhc_version, qualifier => "-f ${ups_flavor} -q python27";
    }

}
