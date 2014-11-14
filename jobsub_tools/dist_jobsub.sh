#!/bin/sh 
VERS=v1_3
REV=_1_1_3
./make_tablefile.py $VERS$REV

if [ "$1" ==  "" ]; then
	echo "usage $0 target_machine"
	echo "tars up jobsub_tools and distributes it to /fnal/ups/prd"
	exit -1
fi
cp ../lib/JobsubConfigParser/* prd/jobsub_tools/${VERS}/Linux-2/pylib/JobsubConfigParser/
cp ../server/conf/jobsub.ini prd/jobsub_tools/${VERS}/Linux-2/bin
cd ups_db
tar cvf db.jobsub_tools.tar jobsub_tools --exclude  ".svn" --exclude "jobsub_tools/.svn/"
scp db.jobsub_tools.tar products@$1.fnal.gov:/fnal/ups/db
ssh products@$1.fnal.gov "cd /fnal/ups/db;  tar xvf db.jobsub_tools.tar; rm db.jobsub_tools.tar; rm jobsub_tools/${VERS}c.fifebatch.version"
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

scp prd.jobsub_tools.tar products@$1.fnal.gov:/fnal/ups/prd
CMD="cd /fnal/ups/prd; mkdir -p jobsub_tools/$VERS$REV; rm -rf jobsub_tools/$VERS$REV/* ; mkdir -p tmp; cd tmp; rm -rf *; tar xvf ../prd.jobsub_tools.tar ; cd ..; mv tmp/jobsub_tools/$VERS/Linux-2 jobsub_tools/$VERS$REV; chmod -R g+w jobsub_tools/$VERS$REV; rm prd.jobsub_tools.tar; rm -rf tmp"
echo "performing $CMD on $1"
ssh products@$1.fnal.gov $CMD 
rm prd.jobsub_tools.tar
cd ..

