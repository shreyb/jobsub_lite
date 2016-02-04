#!/usr/bin/env python
# $Id$
import os
import sys
import subprocess


class JobUtils(object):
    def __init__(self):
        pass

    def getstatusoutput(self,cmd,yakFlag=False):
        proc = subprocess.Popen(cmd,shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        retVal = proc.wait()
        #val= "%s"%os.getpid()+" "
        val=""
        for op in proc.stdout:
            val=val+op.rstrip()
        if yakFlag:
            print "\n\nJobUtils output is %s\n---DONE---\n" %(val)
        return(retVal,val)

    def ifdhString(self):
        fs="""cat << '_HEREDOC_' > %s
#!/bin/sh
#
which ifdh > /dev/null 2>&1
has_ifdh=$?
if [ "$has_ifdh" -ne "0" ] ; then
    unset PRODUCTS
    for setup_file in %s ; do
      if [ -e "$setup_file" ] && [ "$has_ifdh" -ne "0" ]; then
         source $setup_file
         ups exist ifdhc $IFDH_VERSION
         has_ifdh=$?
         if [ "$has_ifdh" = "0" ] ; then
             setup ifdhc $IFDH_VERSION
             break
         else
            unset PRODUCTS
         fi
     fi
   done
fi
which ifdh > /dev/null 2>&1
if [ "$?" -ne "0" ] ; then
    echo "Can not find ifdh version $IFDH_VERSION in cvmfs"
else
    ifdh "$@"
fi
_HEREDOC_
chmod +x %s
            """        
        return fs

    def krb5ccNameString(self):
        ks = """
if [ "${KRB5CCNAME}" != "" ]; then
   BK=`basename ${KRB5CCNAME}`
   if [ -e "${_CONDOR_JOB_IWD}/${BK}" ]; then
      export KRB5CCNAME="${_CONDOR_JOB_IWD}/${BK}"
      chmod 400 ${KRB5CCNAME}
      (while [ 0 ]; do kinit -R; sleep 3600 ; done ) &
   fi
fi
            """
        return ks

    def logTruncateString(self):
        lts = """
function is_set {
  [ "$1" != "" ]
  RSLT=$?
  return $RSLT
}
    
function get_log_sizes {
    total=$JOBSUB_MAX_JOBLOG_SIZE
    head=$JOBSUB_MAX_JOBLOG_HEAD_SIZE
    tail=$JOBSUB_MAX_JOBLOG_TAIL_SIZE

    if (( is_set $head) && ( is_set $tail )); then
         total=$(($head + $tail))   
    elif ( is_set $total ); then
            if ((  is_set $head ) && (($total > $head))); then
                tail=$(($total - $head))
                total=$((head + tail))
            elif ((  is_set $tail ) && (($total > $tail))); then
                head=$(($total - $tail))
                total=$((head + tail))
            else
                head=$(( $total / 5 ))
                tail=$(( 4 * $total / 5))
            fi
    else
        total=5000000
        head=1000000        
        tail=4000000
    fi
    export JOBSUB_MAX_JOBLOG_SIZE=$total
    export JOBSUB_MAX_JOBLOG_HEAD_SIZE=$head
    export JOBSUB_MAX_JOBLOG_TAIL_SIZE=$tail

}
        
function jobsub_truncate {
    get_log_sizes 
    JOBSUB_LOG_SIZE=`wc -c $1 | awk '{print $1}'`
    if ( ! is_set $JSB_TMP );then
            export JSB_TMP=/tmp/$$
        mkdir -p $JSB_TMP
    fi
    JSB_OUT=$JSB_TMP/truncated
    if [ $JOBSUB_LOG_SIZE -gt $JOBSUB_MAX_JOBLOG_SIZE ]; then
        head -c $JOBSUB_MAX_JOBLOG_HEAD_SIZE $1 > $JSB_OUT
        echo "\njobsub:---- truncated after $JOBSUB_MAX_JOBLOG_HEAD_SIZE bytes--\n" >>$JSB_OUT
        echo "\njobsub:---- resumed for last $JOBSUB_MAX_JOBLOG_TAIL_SIZE bytes--\n" >>$JSB_OUT
        tail -c $JOBSUB_MAX_JOBLOG_TAIL_SIZE $1 >> $JSB_OUT
    else
        cp $1 $JSB_OUT
    fi
    cat $JSB_OUT
    rm $JSB_OUT
}
        """
        return lts




    def maketar_sh(self):
        cmpr="""
#!/bin/sh

TMPDIR=`/bin/mktemp -d`
echo "building in $TMPDIR"
CMPRSSDIR=$1
cd $CMPRSSDIR
tar cvzf $CMPRSSDIR.tgz *
cat $HOME/xtrct.sh $CMPRSSDIR.tgz > $TMPDIR/$CMPRSSDIR.sh
rm $CMPRSSDIR.tgz
chmod +x $TMPDIR/$CMPRSSDIR.sh
echo "your submission file is  $TMPDIR/$CMPRSSDIR.sh"
"""
                
        return cmpr
        
    def untar_sh(self):
        xtrct="""
#!/bin/bash
SKIP=`/bin/gawk '/^__TARFILE_FOLLOWS__/ { print NR + 1; exit 0; }' $0`
THIS=$0
# take the tarfile and pipe it into tar
tail -n +$SKIP $THIS | tar -xkz
# run arv[0:$] as a command line
sh  $*
exit 0
# NOTE: Don't place any newline characters after the last line below.
__TARFILE_FOLLOWS__
"""
        return xtrct

        
    def poms_info(self):
        poms_str="""

export NODE_NAME=`hostname`
export BOGOMIPS=`grep bogomips /proc/cpuinfo | tail -1 | cut -d ' ' -f2`
export VENDOR_ID=`grep vendor_id /proc/cpuinfo | tail -1 | cut -d ' ' -f2`
export poms_data='{"campaign_id":"'$CAMPAIGN_ID'","task_definition_id":"'$TASK_DEFINITION_ID'","task_id":"'$POMS_TASK_ID'","job_id":"'$POMS_JOB_ID'","batch_id":"'$JOBSUBJOBID'","host_site":"'$HOST_SITE'","bogomips":"'$BOGOMIPS'","node_name":"'$NODE_NAME'","vendor_id":"'$VENDOR_ID'"}'
echo poms_data:$poms_data

        """
        return poms_str

    def sam_start(self):
        sam_start_str="""

${JSB_TMP}/ifdh.sh startProject $SAM_PROJECT $SAM_STATION $SAM_DATASET $SAM_USER $SAM_GROUP
SPSTATUS=$?
while true; do
    STATION_STATE=$SAM_STATION.`date '+%s'`
    PROJECT_STATE=$SAM_DATASET.`date '+%s'`
    ${JSB_TMP}/ifdh.sh dumpStation $SAM_STATION > $STATION_STATE
    grep $SAM_PROJECT $STATION_STATE > $PROJECT_STATE

    TOTAL_FILES=`cat $PROJECT_STATE | sed "s/^.* contains //" | sed "s/ total files:.*$//"`
    CACHE_MIN=$TOTAL_FILES

    PROJECT_PREFETCH=`grep 'Per-project prefetched files' $STATION_STATE | sed "s/^.* files: //"`
    SCALED_PREFETCH=$[$PROJECT_PREFETCH/2]
    if [ $SCALED_PREFETCH -lt $CACHE_MIN ]; then
        CACHE_MIN=$SCALED_PREFETCH
    fi
    IN_CACHE=`cat $PROJECT_STATE | sed "s/^.*of these //" | sed "s/ in cache.*$//"`
    rm $PROJECT_STATE $STATION_STATE
    if [ $TOTAL_FILES -le 0 ]; then
        echo there are no files in $SAM_DATASET! exiting....
        break
    fi
    if [ $IN_CACHE -ge $CACHE_MIN  ]; then
        echo $IN_CACHE files of $TOTAL_FILES are staged, exiting
        break
    fi
    sleep 60

done

        """
        return sam_start_str

    def print_usage(self):
        usage = """
                This method should never be called.  Please open a service desk ticket
                """ 

        print usage
