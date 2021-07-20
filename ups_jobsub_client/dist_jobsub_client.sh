#!/bin/sh 
if [ "$#" != "3" ] ; then
	echo "usage $0 target_machine release-version url-to-tarball"
	echo "tars up $PRD_NM and distributes it to /fnal/ups/prd"
        echo "example: have just built "
        echo "\$HOME/0.2.rc2/jobsub-client-v0.2.rc2.tgz using release.py"
        echo "and wish to install it on novagpvm01:"
        echo ""
        echo "./dist_$PRD_NM.sh novagpvm01 v0.2.rc2 \$HOME/0.2.rc2/jobsub-client-v0.2.rc2.tgz "
	exit -1
fi

TGT_HOST=$1
VERS=$2
TARBALL_LOCATION=$3

[ "$PRD_NM" = "" ] && PRD_NM=jobsub_client
[ "$UPS_TDIR" = "" ] && UPS_TDIR=/fnal/ups
UPS_DB=$UPS_TDIR/db/$PRD_NM
UPS_PRD=$UPS_TDIR/prd/$PRD_NM
UPS_TMP=/tmp/$PRD_NM
UPS_TMP_DB=$UPS_TMP/ups/db
UPS_TMP_PRD=$UPS_TMP/ups/prd
cd `dirname $0`
mkdir -p ups_db/$PRD_NM
if [ -e jobsub ]; then
	rm -rf jobsub
fi
./make_tablefile.py $VERS

cd ups_db
tar cf db.$PRD_NM.tar $PRD_NM
ssh products@$TGT_HOST rm -rf  $UPS_TMP
ssh products@$TGT_HOST "mkdir -p $UPS_TMP_DB; mkdir -p $UPS_TMP_PRD"
scp db.$PRD_NM.tar products@$TGT_HOST:$UPS_TMP_DB
ssh products@$TGT_HOST "cd $UPS_TMP_DB; tar xf db.$PRD_NM.tar; rm db.$PRD_NM.tar" 
rm  db.$PRD_NM.tar
cd -
if [ -e "$TARBALL_LOCATION" ] ; then
    cp $TARBALL_LOCATION .
else
    wget $TARBALL_LOCATION
fi
TARBALL=`basename $TARBALL_LOCATION`
tar xzf $TARBALL
rm $TARBALL
mv jobsub/client jobsub/$PRD_NM
cp jobsub/doc/release.notes jobsub/$PRD_NM
mkdir -p jobsub/$PRD_NM/ups
mkdir -p jobsub/$PRD_NM/__pycache__
cd jobsub
tar cf prd.$PRD_NM.tar $PRD_NM
scp prd.$PRD_NM.tar products@$TGT_HOST:$UPS_TMP_PRD
CMD="cd $UPS_TMP_PRD; tar xf prd.$PRD_NM.tar; rm prd.$PRD_NM.tar"

ssh products@$TGT_HOST $CMD
CMD="cd $UPS_DB; cp -rf $UPS_TMP_DB/$PRD_NM/* ."
ssh products@$TGT_HOST $CMD
CMD="rm -rf $UPS_PRD/$VERS; mkdir -p $UPS_PRD/$VERS/NULL; cp -rf $UPS_TMP_PRD/$PRD_NM/* $UPS_PRD/$VERS/NULL;"
ssh products@$TGT_HOST $CMD
