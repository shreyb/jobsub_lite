#!/bin/sh
yell() { echo "$0: $*" >&2; }
die() { yell "$*"; exit 111; }
try() { echo "$@"; "$@" || die "FAILED $*"; }

thisdir=`pwd`
packagedir=`dirname $0`
try cd $packagedir
try source ./release-all.env.sh

cd ..
if [ "$PRACTICE_RUN" = "" ]; then
    EXE=try
else
    EXE=/bin/echo
fi

if [ "$RC" = "" ]; then
    if [ "$RPMR" = "" ]; then
        echo " RC or RPMR (release cand number) OR (rpm number) must be set"
        echo " edit release-all.env.sh and try again"
        exit 1
    fi
    RVER=${VER}
    RPMVER=${VER}-${RPMR}
    JTMVER=${TOOL_MVER}
    JTVER=${TOOL_VER}_${JTMVER}
    RC_CMD=" --rpm-release=${RPMR} "
else
    RVER=${VER}.rc${RC}
    RPMVER=${RVER}
    JTMVER=${TOOL_MVER}_rc${RC}
    JTVER=${TOOL_VER}_${JTMVER}
    RC_CMD="--rc $RC"
fi
CVER=`echo v${RVER} | sed 's/\./_/g'`
test "$RPMR" && test $RPMR -gt 1
if [ $? -eq 0 ]; then
    CVER="${CVER}_${RPMR}"
fi
RDIR=/var/tmp/$USER

#tag and push to origin
if [  "$TAG_AND_PUSH" != "" ]; then 
   TVER="v${RPMVER}"  
   $EXE git tag  -m ${TVER} -a ${TVER}
   $EXE git push origin ${TVER}
   $EXE git tag  -m jobsub_tools_${JTVER} -a jobsub_tools_${JTVER}
   $EXE git push origin jobsub_tools_${JTVER}
fi

#generate rpm and put in repo
try cd packaging
try test -e release.py
$EXE ./release.py  --version ${VER} --source-dir $HOME/jobsub --release-dir ${RDIR}  ${RC_CMD} 
RPM=`ls ${RDIR}/${RPMVER}/*.rpm 2>/dev/null`
if [ "$RPM" = "" ]; then
    RPM=${RDIR}/${RVER}/jobsub.${RVER}.rpm
fi
$EXE ./populate-rpmrepo.sh $RPM $PROD 

#put jobsub_client in ups/upd
try cd ../ups_jobsub_client/
CLIENT=`ls ${RDIR}/${RVER}/*.tgz 2>/dev/null` 
if [ "$CLIENT" = "" ]; then
    CLIENT=${RDIR}/${RVER}/jobsub_client.${RVER}.tgz
fi
try test -e dist_jobsub_client.sh 
$EXE ./dist_jobsub_client.sh ${UPSNODE} $CVER $CLIENT
CMD="source /fnal/ups/etc/setups.sh; setup ups; setup upd; upd addproduct jobsub_client ${CVER} -f NULL"
echo $CMD > $HOME/jobsub_client_to_ups.sh
$EXE scp $HOME/jobsub_client_to_ups.sh ${UPSNODE}:jobsub_client_to_ups.sh
$EXE ssh ${UPSNODE} 'sh ./jobsub_client_to_ups.sh'

#put jobsub_tools in ups/upd
try cd ../jobsub_tools/
try test -e dist_jobsub.sh
$EXE ./dist_jobsub.sh ${UPSNODE} $TOOL_VER  _${JTMVER}
CMD2="source /fnal/ups/etc/setups.sh; setup ups; setup upd; upd addproduct jobsub_tools ${JTVER}  -f Linux+2"
echo $CMD2 > $HOME/jobsub_tools_to_ups.sh
$EXE scp $HOME/jobsub_tools_to_ups.sh ${UPSNODE}:jobsub_tools_to_ups.sh
$EXE ssh ${UPSNODE} 'sh ./jobsub_tools_to_ups.sh'
cd $thisdir
