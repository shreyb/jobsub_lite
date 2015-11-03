#!/bin/sh 
VERS=v1_4
REV=_1_cli


if [ "$1" != "" ] ; then
    VERS=$1
fi

if [ "$2" != "" ] ; then
    REV=$2
fi
mkdir -p ups_db/jobsub_tools
./make_tablefile.py $VERS$REV
HERE=`pwd`
cp ../lib/JobsubConfigParser/* prd/jobsub_tools/${VERS}/Linux-2/pylib/JobsubConfigParser/
cp ../server/conf/jobsub.ini prd/jobsub_tools/${VERS}/Linux-2/bin
mv  prd/jobsub_tools/VER  prd/jobsub_tools/${VERS}
cd ups_db
tar cvf db.jobsub_tools.tar jobsub_tools --exclude  ".svn" --exclude "jobsub_tools/.svn/"
sudo -u products cp db.jobsub_tools.tar /fnal/ups/db
CMD="cd /fnal/ups/db;  tar xvf db.jobsub_tools.tar; rm db.jobsub_tools.tar; "
echo $CMD > cmd.sh
chmod +x cmd.sh
sudo -u products ./cmd.sh
rm cmd.sh
rm  db.jobsub_tools.tar
cd ../prd
cd jobsub_tools/${VERS}/Linux-2
chmod -R 775 ./bin/condor_wrappers/ ./bin/etc/ ./pylib/groupsettings/ ./test/
cd -
tar cvf prd.jobsub_tools.tar jobsub_tools --exclude .svn \
--exclude ./pylib/.svn \
--exclude ./pylib/groupsettings/.svn \
--exclude ./test/.svn \
--exclude ./bin/.svn \
--exclude ./bin/condor_wrappers/.svn \
--exclude ./bin/etc/.svn

sudo -u products cp  prd.jobsub_tools.tar /fnal/ups/prd
CMD="cd /fnal/ups/prd; mkdir -p jobsub_tools/$VERS$REV; rm -rf jobsub_tools/$VERS$REV/* ; mkdir -p tmp; cd tmp; rm -rf *; tar xvf ../prd.jobsub_tools.tar ; cd ..; mv tmp/jobsub_tools/$VERS/Linux-2 jobsub_tools/$VERS$REV; chmod -R g+w jobsub_tools/$VERS$REV; rm prd.jobsub_tools.tar; rm -rf tmp"
echo $CMD > cmd.sh
chmod +x cmd.sh
sudo -u products ./cmd.sh
rm cmd.sh
rm prd.jobsub_tools.tar
cd ..
cd $HERE
mv  prd/jobsub_tools/${VERS}  prd/jobsub_tools/VER
source /fnal/ups/etc/setups.sh
ups exist jobsub_tools $VERS$REV
