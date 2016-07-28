class jobsub_server::files{
  
     $jobsub_server_version = $jobsub_server::vars::jobsub_server_version
     $jobsub_tools_version = $jobsub_server::vars::jobsub_tools_version
     $jobsub_user = $jobsub_server::vars::jobsub_user
     $jobsub_user_uid = $jobsub_server::vars::jobsub_user_uid
     $jobsub_group = $jobsub_server::vars::jobsub_group
     $jobsub_user_gid = $jobsub_server::vars::jobsub_user_gid
     $jobsub_user_home = $jobsub_server::vars::jobsub_user_home
     $jobsub_basejobsdir = $jobsub_server::vars::jobsub_basejobsdir
     $jobsub_logsbasedir = $jobsub_server::vars::jobsub_logsbasedir
     $jobsub_jobhistory_count = $jobsub_server::vars::jobsub_jobhistory_count
     $jobsub_git_branch = $jobsub_server::vars::jobsub_git_branch
     $jobsub_git_dir = $jobsub_server::vars::jobsub_git_dir
     $jobsub_cert = $jobsub_server::vars::jobsub_cert
     $jobsub_key = $jobsub_server::vars::jobsub_key
     $jenkins_user = $jobsub_server::vars::jenkins_user
     $jenkins_home = $jobsub_server::vars::jenkins_home
     $jenkins_cert = $jobsub_server::vars::jenkins_cert
     $jenkins_key = $jobsub_server::vars::jenkins_key
     $jenkins_admin_email = $jobsub_server::vars::jenkins_admin_email



     $esg = '/etc/grid-security'
 
     exec { 'setupCA':
       command => '/usr/sbin/osg-ca-manage setupCA --location root --url osg',
       require => [ Package['osg-ca-scripts'] ],
       creates => "${esg}/certificates/FNAL-SLCS.pem",
     }
     
     exec { 'makebasedir':
       command => "/bin/mkdir -p ${jobsub_basejobsdir}",
       creates => $jobsub_basejobsdir,
     }
    ######################################################## 
     exec { "${esg}/jobsub":
       command => "/bin/mkdir -p ${esg}/jobsub",
       creates => "${esg}/jobsub",
     }
     
     file {$jobsub_cert :
         owner   => $jobsub_user,
         group   => $jobsub_group,
         mode    => '0444',
         require => Exec['jobsub_cert'],
     }
     
     exec { 'jobsub_cert':
       command => "/bin/cp ${esg}/hostcert.pem ${jobsub_cert}",
       require => Exec["${esg}/jobsub"],
       creates => $jobsub_cert,
     }
     
     file {$jobsub_key :
         owner   => $jobsub_user,
         group   => $jobsub_group,
         mode    => '0400',
         require => Exec['jobsub_key'],
     }

     exec { 'jobsub_key':
       command => "/bin/cp ${esg}/hostkey.pem ${jobsub_key}",
       require => Exec["${esg}/jobsub"],
       creates => $jobsub_key,
     }


      file { $jobsub_basejobsdir:
        ensure => directory,
        owner  => $jobsub_user,
        group  => $jobsub_group,
        mode   => '0755'
      }

      file { "${jobsub_basejobsdir}/proxies":
        ensure => directory,
        owner  => $jobsub_user,
        group  => $jobsub_group,
        mode   => '0700'
      }

      file { "${jobsub_basejobsdir}/uploads":
        ensure => directory,
        owner  => $jobsub_user,
        group  => $jobsub_group,
        mode   => '0775'
      }

      file { "${jobsub_basejobsdir}/history":
        ensure => directory,
        owner  => $jobsub_user,
        group  => $jobsub_group,
        mode   => '0775',
      }

      file { "${jobsub_basejobsdir}/history/jobsub_history.db":
        ensure => file,
        owner  => $jobsub_user,
        group  => $jobsub_group,
        mode   => '0644',
        require => Exec['create_jobsub_history_db'],
      }

      file { "${jobsub_basejobsdir}/history/work":
        ensure => directory,
        owner  => $jobsub_user,
        group  => $jobsub_group,
        mode   => '0775',
      }

      file { "${jobsub_basejobsdir}/history/work/create_jobsub_history_db.sql":
        ensure => file,
        owner  => $jobsub_user,
        group  => $jobsub_group,
        mode   => '0644',
        require => File["${jobsub_basejobsdir}/history/work"],
        content => template('jobsub_server/create_jobsub_history_db.sql.erb'),
      }
 
     $db =  "${jobsub_basejobsdir}/history/jobsub_history.db"
     $sql = "${jobsub_basejobsdir}/history/work/create_jobsub_history_db.sql"

     exec { 'create_jobsub_history_db':
       command => "/usr/bin/sqlite3 ${db} < ${sql} ",
       onlyif  => "/usr/bin/test ! -s ${db}",
     }
   ############################################################
#    exec { "${esg}/jenkins":
#      command => "/bin/mkdir -p ${esg}/jenkins",
#      creates => "${esg}/jenkins",
#    }
     
#    file {$jenkins_cert :
#        owner   => $jenkins_user,
#        group   => $jobsub_group,
#        mode    => '0444',
#        require => Exec['jenkins_cert'],
#    }
     
#    exec { 'jenkins_cert':
#      command => "/bin/cp ${esg}/hostcert.pem ${jenkins_cert}",
#      require => Exec["${esg}/jenkins"],
#      creates => $jenkins_cert,
#    }
     
#    file {$jenkins_key :
#        owner   => $jenkins_user,
#        group   => $jobsub_group,
#        mode    => '0400',
#        require => Exec['jenkins_key'],
#    }

#    exec { 'jenkins_key':
#      command => "/bin/cp ${esg}/hostkey.pem ${jenkins_key}",
#      require => Exec["${esg}/jenkins"],
#      creates => $jenkins_key,
#    }

     ########################################################### 

     file { '/var/lib/jobsub':
       ensure => directory,
       owner  => $jobsub_user,
       group  => $jobsub_group,
       mode   => '0755'
     }

      file { '/var/lib/jobsub/tmp':
        ensure => directory,
        owner  => $jobsub_user,
        group  => $jobsub_group,
        mode   => '0755'
      }

      file { '/var/lib/jobsub/creds':
        ensure => directory,
        owner  => $jobsub_user,
        group  => $jobsub_group,
        mode   => '0755'
      }

      file { '/var/lib/jobsub/creds/certs':
        ensure => directory,
        owner  => $jobsub_user,
        group  => $jobsub_group,
        mode   => '0755'
      }

      file { '/var/lib/jobsub/creds/keytabs':
        ensure => directory,
        owner  => $jobsub_user,
        group  => $jobsub_group,
        mode   => '0755'
      }

      file { '/var/lib/jobsub/creds/krb5cc':
        ensure => directory,
        owner  => $jobsub_user,
        group  => $jobsub_group,
        mode   => '0755'
      }

      file { '/var/lib/jobsub/creds/proxies':
        ensure => directory,
        owner  => $jobsub_user,
        group  => $jobsub_group,
        mode   => '0755'
      }

      file { "${jobsub_basejobsdir}/dropbox":
        ensure => directory,
        owner  => $jobsub_user,
        group  => $jobsub_group,
        mode   => '0755'
      }

      file { "${jobsub_basejobsdir}/uploads/job.log":
        ensure => file,
        owner  => $jobsub_user,
        group  => $jobsub_group,
        mode   => '0775'
      }

      file { 'jobsublogsdir':
        ensure => directory,
        name   => $jobsub_logsbasedir,
        owner  => $jobsub_user,
        group  => $jobsub_group,
        mode   => '0755'
      }

      file { '/var/log/jobsub':
        ensure => link,
        target => $jobsub_logsbasedir
      }

      file { '/etc/httpd':
        ensure => directory,
        owner  => 'root',
        group  => 'root',
        mode   => '0755'
      }

      file { '/etc/httpd/conf.d':
        ensure => directory,
        owner  => 'root',
        group  => 'root',
        mode   => '0755'
      }

      file { '/etc/sysconfig/httpd':
        ensure => file,
        owner  => 'root',
        group  => 'root',
        mode   => '0644'
      }

      file_line {
        'allow_proxy_certs':
         ensure => 'present',
         path   => '/etc/sysconfig/httpd',
         line   => 'export OPENSSL_ALLOW_PROXY_CERTS=1',
      }
      file_line {
        'sudoers':
         ensure => 'present',
         path   => '/etc/sudoers',
         line   => 'rexbatch  ALL=(ALL) NOPASSWD:SETENV: /opt/jobsub/server/webapp/jobsub_priv *',
      }


      file { '/etc/httpd/conf.d/jobsub_api.conf':
        ensure  => 'link',
        target  => '/opt/jobsub/server/conf/jobsub_api.conf',
        require => [ Package['jobsub']],
      }

      file { "${jobsub_user_home}/.k5login" :
        ensure  => file,
        owner   => $jobsub_user,
        group   => $jobsub_group,
        mode    => '0600',
        content => template('jobsub_server/jobsub_user.k5login.erb'),
      }

    
      file { "/etc/sysconfig/iptables" :
        ensure  => file,
        notify  => Service['iptables'],
        owner   => root,
        group   => root,
        mode    => '0600',
        content => template('jobsub_server/etc.sysconfig.iptables.erb'),
      }

      file { "${jobsub_user_home}/.security" :
        ensure => directory,
        owner  => $jobsub_user,
        group  => $jobsub_group,
        mode   => '0644',
      }
   
      file { "${jobsub_user_home}/sync_cmd":
        ensure => file,
        owner   => $jobsub_user,
        group   => $jobsub_group,
        mode    => '0600',
        content => 'rsync $1:.security/* $HOME/.security; rsync $1:/var/lib/jobsub/creds/certs/* /var/lib/jobsub/creds/certs/'
      }

      file { '/etc/condor/config.d/99.local.config':
        ensure  => file,
        owner   => 'condor',
        mode    => '0644',
        require => Package['condor'],
        content => template('jobsub_server/etc.condor.config.d.99.local.config.erb'),
      }

      file { '/opt/jobsub/server/conf/jobsub.ini':
        ensure  => file,
        owner   => $jobsub_user,
        group   => $jobsub_group,
        mode    => '0644',
        content => template('jobsub_server/jobsub.ini.erb'),
      }

      file { '/var/www/html/cigetcertopts.txt':
        ensure  => file,
        owner   => $jobsub_user,
        group   => $jobsub_group,
        mode    => '0644',
        content => template('jobsub_server/cigetcertopts.txt.erb'),
      }

      file { '/etc/httpd/conf.d/ssl.conf':
        ensure  => file,
        owner   => $jobsub_user,
        group   => $jobsub_group,
        mode    => '0644',
        content => template('jobsub_server/ssl.conf.erb'),
      }

      file { '/opt/jobsub/server/conf/jobsub_api.conf':
        ensure  => file,
        owner   => $jobsub_user,
        group   => $jobsub_group,
        mode    => '0644',
        content => template('jobsub_server/jobsub_api.conf.erb'),
      }

      file { '/etc/lcmaps.db':
        ensure  => file,
        mode    => '0644',
        content => template('jobsub_server/lcmaps.db.erb')
      }

#     file { '/etc/sysconfig/jenkins':
#       ensure  => file,
#       mode    => '0644',
#       content => template('jobsub_server/etc.sysconfig.jenkins.erb')
#     }
    
#     file { "${jenkins_home}/config.xml":
#       ensure  => file,
#       owner   => $jenkins_user,
#       group   => $jobsub_group,
#       mode    => '0644',
#       content => template('jobsub_server/var.lib.jenkins.config.xml.erb'),
#     }

#     file { "${jenkins_home}/users/admin/config.xml":
#       ensure  => file,
#       owner   => $jenkins_user,
#       group   => $jobsub_group,
#       mode    => '0644',
#       content => template('jobsub_server/var.lib.jenkins.users.admin.config.xml.erb'),
#     }

#     file {"${jenkins_home}/users":
#       ensure => directory,
#       owner  => $jenkins_user,
#       group  => $jobsub_group,
#       mode   => '0755'
#     }

#     file {"${jenkins_home}/users/admin":
#       ensure => directory,
#       owner  => $jenkins_user,
#       group  => $jobsub_group,
#       mode   => '0755'
#     }

      file {"${esg}/jobsub":
        ensure => directory,
        owner  => $jobsub_user,
        group  => $jobsub_group,
        mode   => '0755'
      }

      file { '/opt/jobsub/server/admin/krbrefresh.sh':
        ensure => present,
        owner  => $jobsub_user,
        group  => $jobsub_group,
        mode   => '0744'
      }

      file { '/opt/jobsub/server/admin/jobsub_preen.sh':
        ensure => present,
        owner  => $jobsub_user,
        group  => $jobsub_group,
        mode   => '0744'
      }

      file {'/etc/lcmaps':
        ensure => 'directory',
        mode   => '0755'
      }

      file { '/etc/lcmaps/lcmaps.db':
        ensure  => 'link',
        target  => '/etc/lcmaps.db',
        require => Package['lcmaps-plugins-gums-client']
      }
}
