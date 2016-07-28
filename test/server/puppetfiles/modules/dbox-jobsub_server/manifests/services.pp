class jobsub_server::services{
  service{'httpd':
    ensure     => true,
    enable     => true,
    hasstatus  => true,
    hasrestart => true,
  }
  service{'condor':
    ensure     => true,
    enable     => true,
    hasstatus  => true,
    hasrestart => true,
  }

 service{'iptables':
    ensure     => true,
    enable     => true,
    hasstatus  => true,
    hasrestart => true,
  }

# service{'jenkins':
#   ensure     => true,
#   enable     => true,
#   hasstatus  => true,
#   hasrestart => true,
# }


  cron {'Refresh the kerberos proxies of users in queue that have kerberos principal older than 3600 seconds (default)':
    ensure  => present,
    command => '/opt/jobsub/server/admin/krbrefresh.sh --refresh-proxies 10800 >> /var/log/jobsub/krbrefresh.log 2>&1' ,
    user    => rexbatch,
    minute  => 54,
    hour    => [4,8,16,20],
    require => File['/opt/jobsub/server/admin/krbrefresh.sh']
  }
  cron {'Copy jobs out of condor history file into jobsub_history database':
    ensure  => present,
    command => '/opt/jobsub/server/admin/fill_jobsub_history.sh --keepUp > /dev/null 2>&1',
    user    => rexbatch,
    minute  => [07,17,27,37,47,57],
  }
  cron {"clean jobs out of jobsub_history database older than ${jobsub_jobhistory_count} days":
    ensure  => present,
    command => "/opt/jobsub/server/admin/fill_jobsub_history.sh --pruneDB ${jobsub_jobhistory_count} > /dev/null 2>&1",
    user    => rexbatch,
    hour    => '11',
    minute  => '09',
  }
  cron { "Cleanup files for jobs that were last modified ${jobsub_jobhistory_count} days ago, logs to LOG_DIR/jobsub_preen.log":
    ensure  => present,
    command => "/opt/jobsub/server/admin/jobsub_preen.sh ${jobsub_basejobsdir}/uploads  ${jobsub_jobhistory_count} >> /var/log/jobsub/jobsub_preen.log 2>&1",
    hour    => '10',
    minute  => '30',
    require => File['/opt/jobsub/server/admin/jobsub_preen.sh']
  }
  cron {'clean the dropbox directories of old jobs':
    ensure  => present,
    command => "/opt/jobsub/server/admin/jobsub_preen.sh ${jobsub_basejobsdir}/dropbox  ${jobsub_jobhistory_count} >> /var/log/jobsub/jobsub_preen.log 2>&1",
    user    => root,
    hour => '10',
    minute  => '34',
  }
  cron {'clean /var/lib/jobsub/tmp of leftover files from failed authentications':
    ensure  => present,
    command => "/opt/jobsub/server/admin/jobsub_preen.sh /var/lib/jobsub/tmp ${jobsub_jobhistory_count}  thisDirOnly >> /var/log/jobsub/jobsub_preen.log 2>&1",
    user    => root,
    hour    => '10',
    minute  => '44',
  }
  cron {'clean /var/lib/jobsub/creds/proxies of expired proxies and cruft from failed authentications':
    ensure  => present,
    command => "/opt/jobsub/server/admin/jobsub_preen.sh /var/lib/jobsub/creds/proxies/ ${jobsub_jobhistory_count}   rmEmptySubdirs   >> /var/log/jobsub/jobsub_preen.log 2>&1",
    user    => root,
    hour    => '10',
    minute  => '54',
  }

}

