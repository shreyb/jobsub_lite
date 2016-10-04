#!/bin/sh 
VERS=$1
REV=''


mkdir -p ups_db/jobsub_client
if [ -e jobsub ]; then
	rm -rf jobsub
fi
./make_tablefile.py $VERS$REV
MK=$?
if [ "${MK}" != "0" ]; then
    exit ${MK}
fi
cd ups_db
tar cvf db.jobsub_client.tar jobsub_client 
sudo -u products cp db.jobsub_client.tar /fnal/ups/db
cmd="cd /fnal/ups/db;  tar xvf db.jobsub_client.tar; rm db.jobsub_client.tar; "
echo $cmd > cmd.sh
chmod +x cmd.sh
sudo -u products ./cmd.sh
rm  db.jobsub_client.tar cmd.sh
cd -
if [ -e "$2" ] ; then
    cp $2 .
else
    wget $2
fi
TARBALL=`basename $2`
tar xzvf $TARBALL
rm $TARBALL
mv jobsub/client jobsub/jobsub_client
cd jobsub
tar cvf prd.jobsub_client.tar jobsub_client 

sudo -u products cp prd.jobsub_client.tar /fnal/ups/prd
CMD="cd /fnal/ups/prd; mkdir -p jobsub_client/$VERS$REV; rm -rf jobsub_client/$VERS$REV/* ; mkdir -p tmp; cd tmp; rm -rf *; tar xvf ../prd.jobsub_client.tar ; cd ..; mv tmp/jobsub_client jobsub_client/$VERS$REV/NULL;mkdir -p jobsub_client/$VERS/NULL/ups; chmod -R g+w jobsub_client/$VERS$REV;rm prd.jobsub_client.tar; rm -rf tmp "
echo $CMD > cmd.sh
chmod +x cmd.sh
sudo -u  products ./cmd.sh
rm prd.jobsub_client.tar cmd.sh
cd ..

