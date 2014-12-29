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
                usage = """Usage: %s [args] executable [exec_args]
          Possible [args]:

           Generic stuff:
                  -h                         Print this help.

                  -n                         Create the .cmd file and output its name, but
                                                 do not submit the job(s).  You can later submit
                                                 the job with:
                                                         condor_submit <cmd_file>

                  -N <num>           Submit <num> copies of the job.  Each job will
                                                 have access to the environment variable
                                                 $PROCESS that provides the job number (0 to
                                                 <num>-1), equivalent to the decimal point in
                                                 the job ID (the '2' in 134567.2).

                  -submit_host <host>
                                                 submit jobs to condor running on <host> . If
                                                 this option is not specified jobs are submitted
                                                 to gpsn01.fnal.gov

                  -DAG                   Use Dagman to schedule the jobs

                  -q                         Only send email notification if the job ends
                                                 with an error.  (Default is always to email.)

                  -Q                         No email notification ever.

                  -T                         Submit as a test job.  Job will run with highest
                                                 possible priority, but you can only have one such
                                                 job in the queue at a time.

                  -L                         Log file to hold log output from job.


           Environment:
                  -c <ClassAd>   Add condition <ClassAd> to the job.  (See
                                                 documentation on Condor ClassAds for more.)

                  -e <var>           Pass the existing environment variable <var>
                                                 into the job.  (No "$", e.g.: "-e MYVAR".)

                  -l <line>          [Expert option]  Add the line <line> to the
                                                 Condor submission (.cmd) file.  See Condor
                                                 help for more.

           Grid running:
                  -g                         Run the job on the FNAL Grid.

          -opportunistic  Use opportunistic grid slots if available

                  -X509_USER_PROXY <proxy>
                                                 Use a different proxy than the default value.
                                                 The default value is /scratch/$USER/grid/$USER.proxy
                                                 which will be used without this option
                                                 However, some users belong to more than one 
                                                 experiment and set up (for instance)
                                                 /scratch/$USER/grid/$USER.lbne.proxy and
                                                 /scratch/$USER/grid/$USER.nova.proxy to run
                                                 on the grid with different experiment gids

                  -d<tag> <dir>  Writable directory $CONDOR_DIR_<tag> will
                                                 exist on the execution node.  After job completion,
                                                 its contents will be moved to <dir> automatically
                                                 Specify as many <tag>/<dir> pairs as you need.

                  -f <file>          input file <file> will be copied to directory  
                                                 $CONDOR_DIR_INPUT on the execution node.  
                                                 Example :-f /grid/data/minerva/my/input/file.xxx  
                                                 will be copied to $CONDOR_DIR_INPUT/file.xxx 
                                                 Specify as many -f file1 -f file2 args as you need.

                   -USE_GFTP         use globus ftp commands to perform -d and -f file
                                                 transfers instead of default cpn .  Works
                                                 on off site grids AND copies over files with your
                                                 own uid (instead of minervaana). Slower than CPN
                                                 if using common mount point like BLUEARC


           AFS flags.  You should never need any of these:
                  -a                         If -g, then require true AFS on Grid node rather
                                                 than using Parrot to get to minossoft and ups AFS
                                                 areas.  You shouldn't need to use this.  Greatly
                                                 limits the number of nodes available to you.

                  -p                         Run job under Parrot.  Automatically selected
                                                 when running on Grid (-g), so you should never
                                                 need to set this option explicitly.

                  -pOFF                  Do NOT use Parrot when running on the Grid.  Your
                                                 job will not have AFS access in general.  This
                                                 setting is available mostly for testing.  You
                                                 shouldn't need to use -pOFF.

           Miscellaneous:
                  -G <group>         Submit job under group <group>.  This is to allow
                                                 high priority submission for batch production and
                                                 critical analysis tasks.  (Use of groups requires
                                                 express permission.)


           NOTES:
                 You can have as many instances of -c, -d, -e, -l and -y as you need.

                 The -d directory mapping works on non-Grid nodes, too.  
                """ % os.path.basename(sys.argv[0])

                print usage
