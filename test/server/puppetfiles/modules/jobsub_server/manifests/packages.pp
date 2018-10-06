class jobsub_server::packages (String $ifdhc_version = $jobsub_server::vars::ifdhc_version,
                               String $jobsub_tools_version = $jobsub_server::vars::jobsub_tools_version,
                               String $ups_version = $jobsub_server::vars::ups_version,
                               String $ups_flavor = $jobsub_server::vars::ups_flavor ) {
    yumrepo { 'jobsub':
      baseurl  => 'http://jobsub.fnal.gov/rpms/dev/6/$basearch/',
      descr    => 'Jobsub',
      enabled  => 1,
      gpgcheck => 0,
    }

    package { 'epel-release.noarch':
      ensure   => 'installed',
      provider => 'rpm',
      source   => "$jobsub_server::vars::epel_url",
    }

    package { 'osg-release.noarch':
      ensure   => 'installed',
      provider => 'rpm',
      source   => "$jobsub_server::vars::osg_url",
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
      require         => Package['voms-clients-cpp'],
    }

    package { 'voms-clients-cpp':
      install_options => '--enablerepo=osg',
    }

  

}
