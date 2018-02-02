class jobsub_server::users{

    group { $jobsub_server::vars::jobsub_group:
      ensure => present,
      gid    => $jobsub_server::vars::jobsub_user_gid,
    }

    user { $jobsub_server::vars::jobsub_user:
      ensure     => present,
      groups     => $jobsub_server::vars::jobsub_group,
      home       => $jobsub_server::vars::jobsub_user_home,
      managehome => true,
      uid        => $jobsub_server::vars::jobsub_user_uid,
      gid        => $jobsub_server::vars::jobsub_user_gid,
      shell      => '/bin/bash',
      require    => Group[$jobsub_server::vars::jobsub_group]
    }

    user { $jobsub_server::vars::jenkins_user:
      ensure  => present,
      groups  => $jobsub_server::vars::jobsub_group,
      home    => $jobsub_server::vars::jenkins_home,
      uid     => $jobsub_server::vars::jenkins_user_uid,
      gid     => $jobsub_server::vars::jobsub_user_gid,
      shell   => '/bin/bash',
      require => Group[$jobsub_server::vars::jobsub_group]
    }

    user { 'dbox':
      ensure     => present,
      shell      => '/bin/bash',
    }
    user { 'sbaht':
      ensure     => present,
      shell      => '/bin/bash',
    }
    #getent passwd | grep pro: | perl -ne '@a=split(":"); $g="_$a[0]_"; $u="_$a[0]_"; $g=~s/pro//; print "     group{ $g: ensure=> present, }\n     user { $u: ensure => present, require => Group[$g], }\n";' | sed "s/_/\'/g"
     group{ 'k': ensure=> present, }
     user { 'kpro': ensure => present, require => Group['k'], }
     group{ 'e898': ensure=> present, }
     user { 'e898pro': ensure => present, require => Group['e898'], }
     group{ 'hcallumi': ensure=> present, }
     user { 'hcallumipro': ensure => present, require => Group['hcallumi'], }
     group{ 'accel': ensure=> present, }
     user { 'accelpro': ensure => present, require => Group['accel'], }
     group{ 'astro': ensure=> present, }
     user { 'astropro': ensure => present, require => Group['astro'], }
     group{ 'cdms': ensure=> present, }
     user { 'cdmspro': ensure => present, require => Group['cdms'], }
     group{ 'hypcp': ensure=> present, }
     user { 'hypcppro': ensure => present, require => Group['hypcp'], }
     group{ 'minbn': ensure=> present, }
     user { 'minbnpro': ensure => present, require => Group['minbn'], }
     group{ 'minos': ensure=> present, }
     user { 'minospro': ensure => present, require => Group['minos'], }
     group{ 'mipp': ensure=> present, }
     user { 'mipppro': ensure => present, require => Group['mipp'], }
     group{ 'numi': ensure=> present, }
     user { 'numipro': ensure => present, require => Group['numi'], }
     group{ 'test': ensure=> present, }
     user { 'testpro': ensure => present, require => Group['test'], }
     group{ 'nova': ensure=> present, }
     user { 'novapro': ensure => present, require => Group['nova'], }
     group{ 'auger': ensure=> present, }
     user { 'augerpro': ensure => present, require => Group['auger'], }
     group{ 'dzero': ensure=> present, }
     user { 'dzeropro': ensure => present, require => Group['dzero'], }
     group{ 'fermi': ensure=> present, }
     user { 'fermipro': ensure => present, require => Group['fermi'], }
     group{ 'minerva': ensure=> present, }
     user { 'minervapro': ensure => present, require => Group['minerva'], }
     group{ 'lbne': ensure=> present, }
     user { 'lbnepro': ensure => present, require => Group['lbne'], }
     group{ 'argoneut': ensure=> present, }
     user { 'argoneutpro': ensure => present, require => Group['argoneut'], }
     group{ 'mu2e': ensure=> present, }
     user { 'mu2epro': ensure => present, require => Group['mu2e'], }
     group{ 'map': ensure=> present, }
     user { 'mappro': ensure => present, require => Group['map'], }
     group{ 'icecube': ensure=> present, }
     user { 'icecubepro': ensure => present, require => Group['icecube'], }
     group{ 'uboone': ensure=> present, }
     user { 'uboonepro': ensure => present, require => Group['uboone'], }
     group{ 'gm2': ensure=> present, }
     user { 'gm2pro': ensure => present, require => Group['gm2'], }
     group{ 'ilc': ensure=> present, }
     user { 'ilcpro': ensure => present, require => Group['ilc'], }
     group{ 'orka': ensure=> present, }
     user { 'orkapro': ensure => present, require => Group['orka'], }
     group{ 'seaquest': ensure=> present, }
     user { 'seaquestpro': ensure => present, require => Group['seaquest'], }
     group{ 'darkside': ensure=> present, }
     user { 'darksidepro': ensure => present, require => Group['darkside'], }
     group{ 'coupp': ensure=> present, }
     user { 'coupppro': ensure => present, require => Group['coupp'], }
     group{ 'lar1': ensure=> present, }
     user { 'lar1pro': ensure => present, require => Group['lar1'], }
     group{ 'lariat': ensure=> present, }
     user { 'lariatpro': ensure => present, require => Group['lariat'], }
     group{ 'belle': ensure=> present, }
     user { 'bellepro': ensure => present, require => Group['belle'], }
     group{ 'genie': ensure=> present, }
     user { 'geniepro': ensure => present, require => Group['genie'], }
     group{ 'lsst': ensure=> present, }
     user { 'lsstpro': ensure => present, require => Group['lsst'], }
     group{ 'lar1nd': ensure=> present, }
     user { 'lar1ndpro': ensure => present, require => Group['lar1nd'], }
     group{ 'numix': ensure=> present, }
     user { 'numixpro': ensure => present, require => Group['numix'], }
     group{ 'holometer': ensure=> present, }
     user { 'holometerpro': ensure => present, require => Group['holometer'], }
     group{ 'chips': ensure=> present, }
     user { 'chipspro': ensure => present, require => Group['chips'], }
     group{ 'marsaccel': ensure=> present, }
     user { 'marsaccelpro': ensure => present, require => Group['marsaccel'], }
     group{ 'annie': ensure=> present, }
     user { 'anniepro': ensure => present, require => Group['annie'], }
     group{ 'dune': ensure=> present, }
     user { 'dunepro': ensure => present, require => Group['dune'], }
     group{ 'gendetrd': ensure=> present, }
     user { 'gendetrdpro': ensure => present, require => Group['gendetrd'], }
     group{ 'cdf': ensure=> present, }
     user { 'cdfpro': ensure => present, require => Group['cdf'], }
     group{ 'captmnv': ensure=> present, }
     user { 'captmnvpro': ensure => present, require => Group['captmnv'], }
     group{ 'redtop': ensure=> present, }
     user { 'redtoppro': ensure => present, require => Group['redtop'], }
     group{ 'sbnd': ensure=> present, }
     user { 'sbndpro': ensure => present, require => Group['sbnd'], }
     group{ 'next': ensure=> present, }
     user { 'nextpro': ensure => present, require => Group['next'], }
     group{ 'noble': ensure=> present, }
     user { 'noblepro': ensure => present, require => Group['noble'], }
     group{ 'icarus': ensure=> present, }
     user { 'icaruspro': ensure => present, require => Group['icarus'], }
     group{ 'des': ensure=> present, }
     user { 'despro': ensure => present, require => Group['des'], }
     group{ 'admx': ensure=> present, }
     user { 'admxpro': ensure => present, require => Group['admx'], }

}
