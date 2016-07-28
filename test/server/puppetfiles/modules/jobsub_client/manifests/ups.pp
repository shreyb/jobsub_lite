class jobsub_client::ups {

    define product( String $version="", String $qualifier="", String $ensure="" ){
      $cmd = '/bin/su products -c '
      $ups = '. /fnal/ups/etc/setups.sh; setup ups; setup upd; '
      $install = ' upd install '
      $declare = ' ups declare -c '


      exec { "install_${title}":
        command => "${cmd} \"${ups} ${install} ${title} ${version} ${qualifier} \" ",
        require => [ Package['upsupdbootstrap-fnal'], ],
        creates => "/fnal/ups/db/${title}/${version}.table",
      }

      exec { "make_current_${title}":
        command => "${cmd} \"${ups} ${declare} ${title} ${version} ${qualifier}\" ",
        require => [ Package['upsupdbootstrap-fnal'],
                     Exec["install_${title}"] ],
        unless  => "${cmd} \"${ups} ups exist ${title} ${version} ${qualifier} -c \" " ,
      }

    }
}
