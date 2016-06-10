#!/bin/sh

GREPLIST="GROUP= MACH= X509_USER_CERT= X509_USER_KEY="
for OPT in "$@" ; do
    for ITM in ${GREPLIST}; do
        echo $OPT | grep $ITM > /dev/null 2>&1
        if [ $? = 0 ] ;then
            echo export $OPT
            export $OPT
        fi
    done
done

function curl_submit {
   URL="$@"
   cmd_pt=`echo $URL | sed 's/.*:8443/x./' | sed 's/\//\./g'| sed 's/\?//g' | sed 's/\@/\./g' | sed 's/\=//' | sed 's/\.$//' `
   outfile="${GROUP}/${MACH}.html${cmd_pt}.out"
   echo $URL | grep http > /dev/null 2>&1
   if [ $? -ne 0 ] ; then
       URL=" https://${MACH}.fnal.gov:8443${URL} "
   fi
   cmd="curl ${GET_FLAGS} ${URL} "

   echo "${URL}"
   echo $cmd > $outfile 
   echo '--------------------------------------------------' >> $outfile
   bash -c "$cmd" >> $outfile 2>&1
   stat=$?
   if [ "$stat" != "0" ]; then
       echo $cmd returned status $stat
       echo $cmd returned status $stat  >> $outfile 2>&1
       echo FAILED
       exit $stat
   fi
}


if [ "$MACH" = "" ]; then
    MACH=fifebatch
fi

if [[ "${GROUP}" = "" && "$JOBSUB_GROUP" = "" ]]; then
    GROUP=nova
fi
if [ "$JOBSUB_GROUP" != "" ]; then
    GROUP=$JOBSUB_GROUP
fi

MACH=`echo $MACH | sed -e s/.fnal.gov//`
FQDN=$MACH.fnal.gov

if [ "$X509_USER_PROXY" = "" ]; then
    kx509
    X509_USER_PROXY=/tmp/x509up_u${UID}
fi

if [ "$X509_USER_CERT" = "" ]; then
    X509_USER_CERT=$X509_USER_PROXY
    X509_USER_KEY=$X509_USER_PROXY
fi

GET_FLAGS=" -v --tlsv1 -s -i --cacert  /etc/pki/tls/certs/ca-bundle.crt "
GET_FLAGS=${GET_FLAGS}" --cert "${X509_USER_CERT}" "
GET_FLAGS=${GET_FLAGS}" --key  "${X509_USER_KEY}"  -k "
GET_FLAGS=${GET_FLAGS}"  -H 'Accept: text/html' -X GET "
#GET_FLAGS=${GET_FLAGS}" -X GET "

#all the GET URLS in JobSub-API-v0.4.pdf
GET_URLS="            /jobsub/acctgroups/ "
GET_URLS=${GET_URLS}" /jobsub/acctgroups/${GROUP}/ "
GET_URLS=${GET_URLS}" /jobsub/acctgroups/${GROUP}/help/ "
GET_URLS=${GET_URLS}" /jobsub/acctgroups/${GROUP}/jobs/ "
GET_URLS=${GET_URLS}" /jobsub/acctgroups/${GROUP}/jobs/hold/ "
GET_URLS=${GET_URLS}" /jobsub/acctgroups/${GROUP}/jobs/1.0@${MACH}.fnal.gov/ "
GET_URLS=${GET_URLS}" /jobsub/users/ "
GET_URLS=${GET_URLS}" /jobsub/users/${USER}/ "
GET_URLS=${GET_URLS}" /jobsub/users/${USER}/jobs/ "
GET_URLS=${GET_URLS}" /jobsub/users/${USER}/jobs/hold/ "
GET_URLS=${GET_URLS}" /jobsub/users/${USER}/jobs/long/ "
#this one is a typo, should be 'dags' not 'dag'
#throws an exception visible in output but returns
# a 200/OK usersjobs.py:default
GET_URLS=${GET_URLS}" /jobsub/users/${USER}/jobs/dag/ "

#some GET URLS that deliberately won't work to test 404 or not

GET_URLS=${GET_URLS}" /jobsub/acctgroups/group_doesnt_exist/ "
#this one returns a 500 Internal Server error in job.py:index, 
#it should be a 404 not found
GET_URLS=${GET_URLS}" /jobsub/acctgroups/group_doesnt_exist/jobs/ "
GET_URLS=${GET_URLS}" /jobsub/acctgroups/group_doesnt_exist/help/ "
GET_URLS=${GET_URLS}" /jobsub/acctgroups/${GROUP}/resource_doesnt_exist/ "
GET_URLS=${GET_URLS}" /jobsub/users/user_doesnt_exist/ "
GET_URLS=${GET_URLS}" /jobsub/users/user_doesnt_exist/jobs/ "


#some GET URLS that are implemented but not documented - put in JobSub-API-v0.5.pdf
#this is ticket #5929

GET_URLS=${GET_URLS}" /jobsub/acctgroups/${GROUP}/jobs/history/ "
GET_URLS=${GET_URLS}" /jobsub/acctgroups/${GROUP}/users/${USER}/jobs/history/ "
GET_URLS=${GET_URLS}" /jobsub/acctgroups/${GROUP}/users/${USER}/jobs/history/?job_id=1.0@${MACH}.fnal.gov "
GET_URLS=${GET_URLS}" /jobsub/acctgroups/${GROUP}/users/${USER}/jobs/history/1.0@${MACH}.fnal.gov/ "
GET_URLS=${GET_URLS}" /jobsub/jobs/ "
GET_URLS=${GET_URLS}" /jobsub/jobs/summary/ "
GET_URLS=${GET_URLS}" /jobsub/jobs/hold/ "
GET_URLS=${GET_URLS}" /jobsub/version/ "
GET_URLS=${GET_URLS}" /jobsub/acctgroups/${GROUP}/jobs/job_doesnt_exist/sandbox/ "
GET_URLS=${GET_URLS}" /jobsub/acctgroups/${GROUP}/sandboxes/${USER}/ "
GET_URLS=${GET_URLS}" /jobsub/acctgroups/${GROUP}/jobs/dag/help/ "
GET_URLS=${GET_URLS}" /jobsub/acctgroups/${GROUP}/jobs/1.0@${MACH}.fnal.gov/betteranalyze/"
GET_URLS=${GET_URLS}" /jobsub/scheddload/"

mkdir -p ${GROUP}
for URL in ${GET_URLS}; do
   curl_submit $URL
done

for URL in `cat ${FQDN}.${GROUP}.urls_covered.log`; do
    curl_submit $URL
done

echo
echo 
echo quick and dirty report of which pages are implemented or not
echo
grep '< HTTP/1.1' ${GROUP}/${MACH}*out
grep '< HTTP/1.1' ${GROUP}/${MACH}*out | cut -d ' ' -f2-5 | sort | uniq -c
grep 'Exception ' ${GROUP}/${MACH}*.out
if [ $? = 0 ] ; then
    echo 'FAILED'
    exit 1
fi
echo PASSED
exit 0
