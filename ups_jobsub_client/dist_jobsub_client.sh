#!/bin/sh 
if [ "$#" != "3" ] ; then
	echo "usage $0 target_machine release-version url-to-tarball"
	echo "tars up jobsub_client and distributes it to /fnal/ups/prd"
        echo "example: have just built "
        echo "\$HOME/0.2.rc2/jobsub-client-v0.2.rc2.tgz using release.py"
        echo "and wish to install it on novagpvm01:"
        echo ""
        echo "./dist_jobsub_client.sh novagpvm01 v0.2.rc2 \$HOME/0.2.rc2/jobsub-client-v0.2.rc2.tgz "
	exit -1
fi
VERS=$2
REV=''


mkdir -p ups_db/jobsub_client
if [ -e jobsub ]; then
	rm -rf jobsub
fi
./make_tablefile.py $VERS$REV
cd ups_db
tar cvf db.jobsub_client.tar jobsub_client 
scp db.jobsub_client.tar products@$1.fnal.gov:/fnal/ups/db
ssh products@$1.fnal.gov "cd /fnal/ups/db;  tar xvf db.jobsub_client.tar; rm db.jobsub_client.tar; "
rm  db.jobsub_client.tar
cd -
if [ -e "$3" ] ; then
    cp $3 .
else
    wget $3
fi
TARBALL=`basename $3`
tar xzvf $TARBALL
rm $TARBALL
mv jobsub/client jobsub/jobsub_client
cp jobsub/doc/release.notes jobsub/jobsub_client
cd jobsub
tar cvf prd.jobsub_client.tar jobsub_client 

scp prd.jobsub_client.tar products@$1.fnal.gov:/fnal/ups/prd
CMD="cd /fnal/ups/prd; mkdir -p jobsub_client/$VERS$REV; rm -rf jobsub_client/$VERS$REV/* ; mkdir -p tmp; cd tmp; rm -rf *; tar xvf ../prd.jobsub_client.tar ; cd ..; mv tmp/jobsub_client jobsub_client/$VERS$REV/NULL;mkdir -p jobsub_client/$VERS/NULL/ups; chmod -R g+w jobsub_client/$VERS$REV;rm prd.jobsub_client.tar; rm -rf tmp "
echo "performing $CMD on $1"
ssh products@$1.fnal.gov $CMD 
rm prd.jobsub_client.tar
cd ..

