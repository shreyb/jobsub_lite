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
      managehome => true,
      uid        => 8351,
      shell      => '/bin/bash',
    }
    #getent passwd | grep pro: | perl -ne '@a=split(":"); $g="_$a[0]_"; $u="_$a[0]_"; $g=~s/pro//; print "     group{ $g: ensure=> present, gid=> $a[3], }\n     user { $u: ensure => present, uid => $a[2], gid => $a[3], require => Group[$g], }\n";' | sed "s/_/\'/g"
    group{ 'nova': ensure=> present, gid=> 47552, }
    user { 'novapro': ensure => present, uid => 47552, gid => 47552, require => Group['nova'], }
    group{ 'auger': ensure=> present, gid=> 5314, }
    user { 'augerpro': ensure => present, uid => 42418, gid => 5314, require => Group['auger'], }
    group{ 'argoneut': ensure=> present, gid=> 9874, }
    user { 'argoneutpro': ensure => present, uid => 44544, gid => 9874, require => Group['argoneut'], }
    group{ 'ilc': ensure=> present, gid=> 9243, }
    user { 'ilcpro': ensure => present, uid => 46464, gid => 9243, require => Group['ilc'], }
    group{ 'mu2e': ensure=> present, gid=> 9914, }
    user { 'mu2epro': ensure => present, uid => 44592, gid => 9914, require => Group['mu2e'], }
    group{ 'lariat': ensure=> present, gid=> 9225, }
    user { 'lariatpro': ensure => present, uid => 48337, gid => 9225, require => Group['lariat'], }
    group{ 'minerva': ensure=> present, gid=> 9555, }
    user { 'minervapro': ensure => present, uid => 43567, gid => 9555, require => Group['minerva'], }
    group{ 'darkside': ensure=> present, gid=> 9985, }
    user { 'darksidepro': ensure => present, uid => 47823, gid => 9985, require => Group['darkside'], }
    group{ 'mipp': ensure=> present, gid=> 6409, }
    user { 'mipppro': ensure => present, uid => 42412, gid => 6409, require => Group['mipp'], }
    group{ 'test': ensure=> present, gid=> 9954, }
    user { 'testpro': ensure => present, uid => 42415, gid => 9954, require => Group['test'], }
    group{ 'orka': ensure=> present, gid=> 9211, }
    user { 'orkapro': ensure => present, uid => 47664, gid => 9211, require => Group['orka'], }
    group{ 'belle': ensure=> present, gid=> 10043, }
    user { 'bellepro': ensure => present, uid => 48347, gid => 10043, require => Group['belle'], }
    group{ 'minbn': ensure=> present, gid=> 5468, }
    user { 'minbnpro': ensure => present, uid => 42410, gid => 5468, require => Group['minbn'], }
    group{ 'dzero': ensure=> present, gid=> 1507, }
    user { 'dzeropro': ensure => present, uid => 42706, gid => 1507, require => Group['dzero'], }
    group{ 'fermi': ensure=> present, gid=> 9767, }
    user { 'fermipro': ensure => present, uid => 43373, gid => 9767, require => Group['fermi'], }
    group{ 'lbne': ensure=> present, gid=> 9960, }
    user { 'lbnepro': ensure => present, uid => 44539, gid => 9960, require => Group['lbne'], }
    group{ 'map': ensure=> present, gid=> 9990, }
    user { 'mappro': ensure => present, uid => 44628, gid => 9990, require => Group['map'], }
    group{ 'coupp': ensure=> present, gid=> 9645, }
    user { 'coupppro': ensure => present, uid => 48270, gid => 9645, require => Group['coupp'], }
    group{ 'cdms': ensure=> present, gid=> 5442, }
    user { 'cdmspro': ensure => present, uid => 42407, gid => 5442, require => Group['cdms'], }
    group{ 'icecube': ensure=> present, gid=> 9851, }
    user { 'icecubepro': ensure => present, uid => 44890, gid => 9851, require => Group['icecube'], }
    group{ 'minos': ensure=> present, gid=> 5111, }
    user { 'minospro': ensure => present, uid => 42411, gid => 5111, require => Group['minos'], }
    group{ 'lar1': ensure=> present, gid=> 9263, }
    user { 'lar1pro': ensure => present, uid => 48311, gid => 9263, require => Group['lar1'], }
    group{ 'genie': ensure=> present, gid=> 9356, }
    user { 'geniepro': ensure => present, uid => 49563, gid => 9356, require => Group['genie'], }
    group{ 'accel': ensure=> present, gid=> 1570, }
    user { 'accelpro': ensure => present, uid => 42405, gid => 1570, require => Group['accel'], }
    group{ 'gm2': ensure=> present, gid=> 9950, }
    user { 'gm2pro': ensure => present, uid => 45651, gid => 9950, require => Group['gm2'], }
    group{ 'theo': ensure=> present, gid=> 1540, }
    user { 'theopro': ensure => present, uid => 42416, gid => 1540, require => Group['theo'], }
    group{ 'uboone': ensure=> present, gid=> 9937, }
    user { 'uboonepro': ensure => present, uid => 45225, gid => 9937, require => Group['uboone'], }
    group{ 'patri': ensure=> present, gid=> 9511, }
    user { 'patripro': ensure => present, uid => 42414, gid => 9511, require => Group['patri'], }
    group{ 'seaquest': ensure=> present, gid=> 6269, }
    user { 'seaquestpro': ensure => present, uid => 47670, gid => 6269, require => Group['seaquest'], }

}
