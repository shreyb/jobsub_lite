#!/bin/bash
#script to generate local schedds on a jobsub_server
#usage for S in nova1 nova2 nova3 cdf1 cdf2 minerva1 minerva2 minerva3 annie1 ; do  local_schedd_gen.sh $S; done

spool=$(condor_config_val spool)
mkdir -p $spool/$1
chown condor:condor $spool/$1
vo=$(echo $1 | sed 's/[0-9]*//g')
cat > $1.conf  << EOF
SCHEDD_$1 = \$(SCHEDD)
SCHEDD_$1_ARGS = -f -local-name $1
SCHEDD_$1_LOG = \$(LOG)/ScheddLog.$1
SCHEDD_$1_SPOOL = \$(SPOOL)/$1
SCHEDD.$1.SCHEDD_NAME = $1@\$(FULL_HOSTNAME)
SCHEDD.$1.SPOOL = \$(SPOOL)/$1
SCHEDD.$1.SCHEDD_LOG = \$(LOG)/ScheddLog.$1
SCHEDD.$1.SCHEDD_ADDRESS_FILE = \$(SPOOL)/.schedd_address_$1
SCHEDD.$1.SCHEDD_DAEMON_AD_FILE = \$(SPOOL)/.schedd_classad_$1
SCHEDD.$1.HISTORY = \$(SPOOL)/history_$1
SCHEDD.$1.InDownTime = False
SCHEDD.$1.SupportedVOList= "$vo"
DAEMON_LIST = \$(DAEMON_LIST), SCHEDD_$1
SYSTEM_VALID_SPOOL_FILES = \$(SYSTEM_VALID_SPOOL_FILES), $1, .schedd_address_$1, .schedd_classad_$1, history_$1
EOF

cp $1.conf /etc/condor/config.d/66.$1.schedd.conf
