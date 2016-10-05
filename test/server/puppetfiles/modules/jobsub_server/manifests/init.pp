# == Class: jobsub_server
#
# Full description of class jobsub_server here.
#
# === Parameters
#
# Document parameters here.
#
# [*sample_parameter*]
#   Explanation of what this parameter affects and what it defaults to.
#   e.g. "Specify one or more upstream ntp servers as an array."
#
# === Variables
#
# Here you should define a list of variables that this module would require.
#
#
# Author Name <author@domain.com>
#
# === Copyright
#
# Copyright 2016 Your name here, unless otherwise noted.
#
class jobsub_server {
    class { 'jobsub_server::vars' : }
    class { 'jobsub_server::packages' : }
    class { 'jobsub_server::users' : }
    class { 'jobsub_server::files' : }
    class { 'jobsub_server::services' : }

}

