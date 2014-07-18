#!/bin/sh

VERSION=20120229

TMPFILE=/tmp/condor_q_`date +%Y%m%d_%H%M%S`_$$
condor_q > ${TMPFILE}

TMPFILETRIM=/tmp/condor_q_`date +%Y%m%d_%H%M%S`_${$}_trim
LINES=`cat ${TMPFILE} | wc -l`
TOHEAD=$(( $LINES - 2 ))
TOTAIL=$(( $LINES - 6 ))
cat ${TMPFILE} | head -$TOHEAD | tail -$TOTAIL > ${TMPFILETRIM}

OWNERLIST="`cat ${TMPFILETRIM} | awk '{if ($2!="gfactory") print $2}' | sort | uniq `"
HEADER=`head -3 ${TMPFILE} | tail -1 | sed 's/-- Submitter: /-- Summary of /'`

# output
echo 
echo "$HEADER"
echo " OWNER        RUN   IDLE   HELD     OLDEST_JOB"
for OWNER in $OWNERLIST
do
  STATUS=`cat ${TMPFILETRIM} | grep $OWNER | grep -v condor_dagman | awk '{if ($6=="I") i++;if ($6=="H") h++;if ($6=="R") r++;printf "%-10s %6d %6d %6d \n", $2, r, i, h}' | tail -1`
  FIRST=`cat ${TMPFILETRIM} | grep $OWNER | head -1 | awk '{printf "%s %s %s %-18s\n",$3,$4,$5,$NF}'`
  echo "$STATUS    $FIRST"
done
TOTALS=`cat ${TMPFILETRIM} | grep -v gfactory | grep -v condor_dagman | awk '{if ($6=="I") i++;if ($6=="H") h++;if ($6=="R") r++;printf "%-10s %6d %6d %6d \n", "TOTALS", r, i, h}' | tail -1`
echo
echo "$TOTALS"

# gfactory
OWNER=gfactory
STATUS=`cat ${TMPFILETRIM} | grep $OWNER | awk '{if ($6=="I") i++;if ($6=="H") h++;if ($6=="R") r++;printf "Farm glideins:  R=%d I=%d H=%d\n", r, i, h}' | tail -1`
echo
echo "$STATUS"
echo

rm ${TMPFILE}
rm ${TMPFILETRIM}

