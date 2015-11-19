#!/bin/sh


TMPFILE=/tmp/condor_q_`date +%Y%m%d_%H%M%S`_$$
condor_q -g | sed '/Schedd:/d' | sed '/ID.*OWNER/d' | sed '/^$/d'| sed '/jobs;/d' > ${TMPFILE}


OWNERLIST="`cat ${TMPFILE} | awk '{print $2}' | sort | uniq `"
# output
echo 
echo " OWNER        RUN   IDLE   HELD     OLDEST_JOB"
for OWNER in $OWNERLIST
do
  STATUS=`cat ${TMPFILE} | grep $OWNER | awk '{if ($6=="I") i++;if ($6=="H") h++;if ($6=="R") r++;printf "%-10s %6d %6d %6d \n", $2, r, i, h}' | tail -1`
  FIRST=`cat ${TMPFILE} | grep $OWNER | head -1 | awk '{printf "%s %s %s %-18s\n",$3,$4,$5,$NF}'`
  echo "$STATUS    $FIRST"
done
TOTALS=`cat ${TMPFILE} |  awk '{if ($6=="I") i++;if ($6=="H") h++;if ($6=="R") r++;printf "%-10s %6d %6d %6d \n", "TOTALS", r, i, h}' | tail -1`
echo
echo "$TOTALS"

# 
RUNNING=`condor_status -claimed | grep glidein | wc -l`
AVAIL=`condor_status -avail | grep glidein | grep -i unclaimed | wc -l`
echo
echo "glidein count: $RUNNING currently servicing jobs, $AVAIL unclaimed "
echo

rm ${TMPFILE}

