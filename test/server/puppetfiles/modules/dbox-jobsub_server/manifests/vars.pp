# author Dennis Box, dbox@fnal.gov
class jobsub_server::vars{
    $jobsub_server_version = '1.2.1.5-0.1.rc1'
    $jobsub_tools_version = 'v1_4_6'
    $jobsub_user = 'rexbatch'
    $jobsub_user_uid = 47535
    $jobsub_group = 'fife'
    $jobsub_user_gid = 9239
    $jobsub_user_home = '/home/rexbatch'
    $jobsub_basejobsdir = '/fife/local/scratch'
    $jobsub_logsbasedir = '/fife/local/scratch/logs'
    $jobsub_jobhistory_count = '30'
    $jobsub_git_branch = 'puppetized_ci'
    $jobsub_git_dir = '/var/tmp/jobsub'
    $jobsub_cert = '/etc/grid-security/jobsub/jobsubcert.pem'
    $jobsub_key = '/etc/grid-security/jobsub/jobsubkey.pem'
    ######################################################
    $jenkins_user = 'jenkins'
    $jenkins_user_uid = 3617
    $jenkins_user_gid = $jobsub_user_gid
    $jenkins_home = '/var/lib/jenkins'
    $jenkins_cert = '/etc/grid-security/jenkins/jenkinscert.pem'
    $jenkins_key = '/etc/grid-security/jenkins/jenkinskey.pem'
    $jenkins_admin_email = 'dbox@fnal.gov'
    $ups_version = 'v5_1_4'
    $ifdhc_version = 'v1_8_5'
    case $::os['release']['major']{
      '5' : {
        $ups_flavor = 'Linux64bit+2.6-2.5'
        $epel_url = 'https://dl.fedoraproject.org/pub/epel/epel-release-latest-5.noarch.rpm'
        $osg_url = 'https://repo.grid.iu.edu/osg/3.2/osg-3.2-el5-release-latest.rpm'
        $wget_opt = '--no-check-certificate'
        $yum_priorities = 'yum-priorities'
      }
      '6' : {
        $ups_flavor = 'Linux64bit+2.6-2.12'
        $epel_url = 'https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm'
        $osg_url = 'https://repo.grid.iu.edu/osg/3.3/osg-3.3-el6-release-latest.rpm'
        $wget_opt = ''
        $yum_priorities = 'yum-plugin-priorities'
      }
      '7' : {
        $ups_flavor = 'Linux64bit+3.10-2.17'
        $epel_url = 'https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm'
        $osg_url = 'https://repo.grid.iu.edu/osg/3.3/osg-3.3-el7-release-latest.rpm'
        $wget_opt = ''
        $yum_priorities = 'yum-plugin-priorities'
      }
      default: {
        $ups_flavor = 'NULL'
        $epel_url = 'NULL'
        $osg_url = 'NULL'
        $wget_opt = 'NULL'
      }
    }

}
