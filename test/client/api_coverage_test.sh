#!/bin/sh

GREPLIST="GROUP= MACH= "
for OPT in "$@" ; do
    for ITM in ${GREPLIST}; do
        echo $OPT | grep $ITM > /dev/null 2>&1
        if [ $? = 0 ] ;then
            echo export $OPT
            export $OPT
        fi
    done
done

if [ "$MACH" = "" ]; then
    MACH=fifebatch
fi

if [ "$GROUP" = "" ]; then
    GROUP=nova
fi

MACH=`echo $MACH | sed -e s/.fnal.gov//`

GET_FLAGS=" -s -i --cacert  /etc/pki/tls/certs/ca-bundle.crt "
GET_FLAGS=${GET_FLAGS}" --cert /tmp/jobsub_x509up_u${UID} "
GET_FLAGS=${GET_FLAGS}" --key  /tmp/jobsub_x509up_u${UID} -k "
GET_FLAGS=${GET_FLAGS}"  -H 'Accept: text/html' -X GET "

#all the GET URLS in JobSub-API-v0.4.pdf
GET_URLS="            /jobsub/acctgroups/ "
GET_URLS=${GET_URLS}" /jobsub/acctgroups/${GROUP}/ "
GET_URLS=${GET_URLS}" /jobsub/acctgroups/${GROUP}/help/ "
GET_URLS=${GET_URLS}" /jobsub/acctgroups/${GROUP}/jobs/ "
GET_URLS=${GET_URLS}" /jobsub/acctgroups/${GROUP}/jobs/1.0@${MACH}.fnal.gov/ "
GET_URLS=${GET_URLS}" /jobsub/users/ "
GET_URLS=${GET_URLS}" /jobsub/users/${USER}/ "
GET_URLS=${GET_URLS}" /jobsub/users/${USER}/jobs/ "

#some GET URLS that deliberately won't work to test 404

GET_URLS=${GET_URLS}" /jobsub/acctgroups/group_doesnt_exist/ "
GET_URLS=${GET_URLS}" /jobsub/acctgroups/${GROUP}/resource_doesnt_exist/ "

#some GET URLS that are implemented but not documented - put in JobSub-API-v0.5.pdf
#this is ticket #5929

GET_URLS=${GET_URLS}" /jobsub/acctgroups/${GROUP}/jobs/history/ "
GET_URLS=${GET_URLS}" /jobsub/acctgroups/${GROUP}/users/${USER}/jobs/history/ "
GET_URLS=${GET_URLS}" /jobsub/acctgroups/${GROUP}/users/${USER}/jobs/history/?job_id=1.0@${MACH}.fnal.gov "
GET_URLS=${GET_URLS}" /jobsub/jobs/ "

#some URLS that need to be implemented and put in the API doc

GET_URLS=${GET_URLS}" /jobsub/version/ "


for URL in ${GET_URLS}; do
   cmd_pt=`echo $URL | tr {'/','.'} | tr {'@','.'}`
   outfile="${MACH}.html${cmd_pt}out"
   cmd="curl $GET_FLAGS https://${MACH}.fnal.gov:8443${URL} "

   echo "https://${MACH}.fnal.gov:8443${URL}"
   echo $cmd > $outfile
   echo '--------------------------------------------------' >> $outfile
   bash -c "$cmd" >> $outfile
done

echo
echo 
echo quick and dirty report of which pages are implemented or not
echo
grep 'HTTP/1.1' ${MACH}.*.out
