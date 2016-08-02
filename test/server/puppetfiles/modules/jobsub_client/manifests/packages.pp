class jobsub_client::packages( String $ups_flavor = $jobsub_client::vars::ups_flavor,
                               String $osg_url = $jobsub_client::vars::osg_url,
                               String $epel_url = $jobsub_client::vars::epel_url,
                             ) {
    $osg_rpm = basename($osg_url)
    $epel_rpm = basename($epel_url)
    $loc = '/var/tmp'

    package { 'osg-release':
      ensure   => 'installed',
      provider => 'rpm',
      source   => "${loc}/${osg_rpm}",
    }

    file { "${loc}/${osg_rpm}":
      require => Exec["${osg_rpm}"],
    }

    exec { "${osg_rpm}":
      command => "/usr/bin/wget ${jobsub_client::vars::wget_opt} ${osg_url} -O ${loc}/${osg_rpm}",
      require => Package['wget'],
      unless  => "/usr/bin/test -s ${loc}/${osg_rpm}",
    }

    package { 'epel-release':
      ensure   => 'installed',
      provider => 'rpm',
      source   => "${loc}/${epel_rpm}",
    }

    file { "${loc}/${epel_rpm}":
      require => Exec["${epel_rpm}"],
    }

    exec { "${epel_rpm}":
      command => "/usr/bin/wget ${jobsub_client::vars::wget_opt} ${epel_url} -O ${loc}/${epel_rpm}",
      require => Package['wget'],
      unless  => "/usr/bin/test -s ${loc}/${epel_rpm}",
    }
    package { 'wget': ensure => present }
    package { $jobsub_client::vars::yum_priorities : ensure => present,}

    package { 'upsupdbootstrap-fnal': ensure => present }
    file {'/fnal/ups/.k5login':
      owner => 'products',
      content => 'dbox@FNAL.GOV',
      require => Package['upsupdbootstrap-fnal'],
    }

    package { 'curl': ensure => present }
    package { 'krb5-fermi-getcert': ensure => present }
      
    package { 'uberftp':
      ensure          => present,
      install_options => '--enablerepo=osg',
    }

    package { 'globus-ftp-client':
      ensure          => present,
      install_options => '--enablerepo=osg',
    }

    package { 'osg-ca-certs':
      ensure          => present,
      install_options => '--enablerepo=osg',
    }

    case $::os['release']['major']{
      '5' : {
        jobsub_client::ups::product { 
          'ups'          : version => $jobsub_client::vars::ups_version, qualifier => "-f ${ups_flavor}";
          'kx509'        : version => $jobsub_client::vars::kx509_version ;
          'jobsub_client': version => $jobsub_client::vars::jobsub_client_version ;
          'ifdhc'        : version => $jobsub_client::vars::ifdhc_version, qualifier => "-f ${ups_flavor} -q python27";
          'git'          : version => 'v1_8_5_3', qualifier => "-f ${ups_flavor}" ; 
          'pycurl'       : version => $jobsub_client::vars::pycurl_version, qualifier=> "-f ${ups_flavor}";
          'python'       : version => $jobsub_client::vars::python_version, qualifier=> "-f ${ups_flavor}";
          'cigetcertlibs': version => $jobsub_client::vars::cigetcert_libs_version, qualifier=> "-f ${ups_flavor}";
          'cigetcert'    : version => $jobsub_client::vars::cigetcert_version , qualifier=> "-f ${ups_flavor}";
        }
      }
      '6' : {
        jobsub_client::ups::product { 
          'ups'          : version => $jobsub_client::vars::ups_version, qualifier => "-f ${ups_flavor}";
          'kx509'        : version => $jobsub_client::vars::kx509_version ;
          'jobsub_client': version => $jobsub_client::vars::jobsub_client_version ;
          'ifdhc'        : version => $jobsub_client::vars::ifdhc_version, qualifier => "-f ${ups_flavor} -q python27";
          'cigetcertlibs': version => $jobsub_client::vars::cigetcert_libs_version, qualifier=> "-f ${ups_flavor}";
          'cigetcert'    : version => $jobsub_client::vars::cigetcert_version , qualifier=> "-f ${ups_flavor}";
        }
      } 
      '7' : {
        jobsub_client::ups::product { 
          'ups'          : version => 'v5_1_7', qualifier => "-f ${ups_flavor}";
          'jobsub_client': version => $jobsub_client::vars::jobsub_client_version ;
          'ifdhc'        : version => 'v1_8_2', qualifier => "-f Linux64bit+3 -q python27";
        }
      }
  }
}
