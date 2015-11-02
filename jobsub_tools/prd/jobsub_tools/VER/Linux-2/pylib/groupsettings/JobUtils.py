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
ifdh "$@"
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

        
        
    def print_usage(self):
        usage = """
                This method should never be called.  Please open a service desk ticket
                """ 

        print usage
