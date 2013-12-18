#!/bin/sh

# Hold and clear arg list
args="$@"
set - ""

# set up for 32 or 64 bit mode
MACH=`uname -m`
if   [ "${MACH}" == "x86_64" ] ; then
  REL="current-x86_64"
elif [  "${MACH}" == "i386" ] ; then
  REL="current-i686"
else
  echo "In parrot init, machine is neither x86_64 nor i386"
  date
  hostname
  uname -a
  uname -m
  printf "Unexpected and fatal!\n"
  exit 1
fi

export PRO=/grid/fermiapp/minos/parrot
export PARROT_DIR=${PRO}/${REL}
export PATH=${PARROT_DIR}/bin:${PATH}
export HTTP_PROXY="http://squid.fnal.gov:3128"

# set u pParrot Temp Directory

[ -d "/local/stage1" ] && mkdir -p /local/stage1/${LOGNAME} 

if [ -r "/local/stage1/${LOGNAME}" ] ; then
  PTD=/local/stage1/${LOGNAME}/parrot # Fermigrid
else
  PTD=/var/tmp/${LOGNAME}/parrot
fi

parrot -m ${PRO}/mountfile.grow -H -t ${PTD} WRAPFILETAG ${args}
