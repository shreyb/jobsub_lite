#!/bin/sh

printf "RUN STARTED  " ; date

SECT=${1}
FUNC=${2}
SECS=${3}

printf "##################################################\n"
printf "#  CHECKING TO SEE WHERE WE ARE AND WHAT WE HAVE #\n"
printf "##################################################\n"

printf "HOSTNAME " ; hostname
#printf "PROBE    VERSION 2008 12 06\n"
#printf "PROBE    VERSION 2009 09 16\n"
printf "PROBE    VERSION 2009 11 05\n"
printf "PWD      " ; pwd
printf "WHOAMI   " ; whoami
printf "ID       " ; id
printf "VENDOR   " ; cat /etc/redhat-release
printf "UNAME    " ; uname  -a
printf "ULIMIT\n"  ; ulimit -a

printf "CORELIMIT "  ; ulimit -c -H

echo
echo PATH  
echo ${PATH} | tr : \\\n
echo SHELL ${SHELL}
echo "tilde" ~
echo "HOME " ${HOME}
df  -h ${HOME}

#  removed this, it was taking several minutes in /grid/home/minerva
#  du -sh ${HOME}

quota -s
if [ -n "${X509_USER_PROXY}" ] ; then
    printf "PROXY    ${X509_USER_PROXY}\n"
    . /usr/local/grid/setup.sh
    voms-proxy-info | grep identity
fi
printf "UMASK "
umask

env | grep CONDOR_SCRATCH_DIR

printf "\n"
printf "######\n"
printf "# ps #\n"
printf "######\n"
printf "\n"

ps -H --forest

# write test to /minerva/data, presently disabled

if [ -r "/minerva/data"    ] ; then
    printf " OK - have /minerva/data \n"
#    date >> /minerva/data/minfarm/PROBE
#    tail    /minerva/data/minfarm/PROBE
fi

[ -r "/minerva/app" ] && printf " OK - have /minerva/app \n"

printf "\n"
printf "##################\n"
printf "# SETTING UP UPS #\n"
printf "##################\n"
printf "\n"

. /usr/local/etc/setups.sh

type setup

printf "\n"
printf "#######\n"
printf "# AFS #\n"
printf "#######\n"
printf "\n"

#if  df /afs  ; then

#printf "\n"
#export MINERVA_SETUP_DIR=/afs/fnal.gov/files/code/e875/general/minervasoft/setup
#fi   # end of AFS

printf "\n"
printf "##################\n"
printf "# /grid/fermiapp #\n"
printf "##################\n"

if  df /grid/fermiapp  ; then

export MINERVA_SETUP_DIR=/grid/fermiapp/software_releases/current_release/
fi   # end of /grid/fermiapp

printf "#######################################\n"
printf "#  SETTING UP THE setup_minerva COMMAND #\n"
printf "#######################################\n"

setup_minerva()
{
. ${MINERVA_SETUP_DIR}/setup.sh $*
}

type setup_minerva
env | grep MINERVA_SETUP_DIR

printf "\n"
printf "##############################################################\n"
printf "#   CHECKING THAT I HAVE A TICKET AND THAT I CAN GET A TOKEN #\n"
printf "##############################################################\n"
printf "\n"

/usr/krb5/bin/klist -f 2>&1
/usr/krb5/bin/aklog    2>&1
/usr/bin/tokens        2>&1

if [ "${FUNC}" = "sleep" ] ; then if [ ${SECS} -gt 0 ] ; then
    printf "#############################\n"
    printf "#  SLEEPING ${SECS} seconds #\n"
    printf "#############################\n"
    { time sleep ${SECS} ; } 2>&1
fi ; fi

if [ "${FUNC}" = "tiny" ]  ; then if [ ${SECS} -gt 0 ] ; then
    printf "#####################################\n"
    printf "#  RUNNING TINY FOR ${SECS} seconds #\n"
    printf "#####################################\n"

    ISEC=`date +%s`
     SEC=0
    { time while [ ${SEC} -lt ${SECS} ] ; do
        /minerva/app/kreymer/condor/tiny/tiny > /dev/null
        (( SEC = `date +%s` - ISEC ))
   done ; } 2>&1
fi ; fi

printf "###################################################\n"
printf "#   CHECKING MY TOKEN AGAIN AT THE END OF THE RUN #\n"
printf "###################################################\n"
printf "\n"

/usr/bin/tokens        2>&1

printf "\n"

if [ -n "${X509_USER_PROXY}" ] ; then
    printf "##########\n"
    printf "#  PROXY #\n"
    printf "##########\n"
    printf "PROXY    ${X509_USER_PROXY}\n"
    . /usr/local/grid/setup.sh
    voms-proxy-info -all
fi

printf "######################################################\n"
printf "#   CHECK THE GRID ENVIRONMENT IF WE ARE ON THE GRID #\n"
printf "######################################################\n"
printf "\n"

if [ -n "${OSG_GRID}" -a -r "${OSG_GRID}/setup.sh" ] ; then

    printf "\n"
    printf "OSG_GRID   ^${OSG_GRID}^\n"
    printf "OSG_DATA   ^${OSG_DATA}^\n"
    printf "OSG_APP    ^${OSG_APP}^\n"
    printf "OSG_WN_TMP ^${OSG_WN_TMP}^\n"
    printf "\n"

    # . ${OSG_GRID}/setup.sh

else

    printf " OK - we do not seem to be on an OSG host \n"

fi

#printf " # # # # # environment # # # # # \n"
#env
#printf " # # # # # environment # # # # # \n"

printf "RUN FINISHED " ; date
