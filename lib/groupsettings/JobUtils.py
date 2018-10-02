#!/usr/bin/env python
# $Id$
import subprocess


class JobUtils(object):

    def __init__(self):
        pass

    def getstatusoutput(self, cmd, yakFlag=False):
        proc = subprocess.Popen(
            cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        retVal = proc.wait()
        #val= "%s"%os.getpid()+" "
        val = ""
        for op in proc.stdout:
            val = val + op.rstrip()
        if yakFlag:
            print "\n\nJobUtils output is %s\n---DONE---\n" % (val)
        return(retVal, val)

    def ifdhString(self):
        fs = """
setup_ifdh_env(){
#
# create ifdh.sh which runs
# ifdh in a seperate environment to
# keep it from interfering with users ifdh set up
#
cat << '_HEREDOC_' > %s
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
    echo "Can not find ifdh version $IFDH_VERSION ,exiting!"
    echo "Can not find ifdh version $IFDH_VERSION ,exiting! ">&2
    exit 1
else
    ifdh "$@"
    exit $?
fi
_HEREDOC_
chmod +x %s
}
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
        lts = r"""
set_jobsub_debug(){
    export PS4='$LINENO:'
    set -xv
}
[[ "$JOBSUB_DEBUG" ]] && set_jobsub_debug



cleanup_condor_dirs(){
if [[ -d "$_CONDOR_JOB_IWD" ]]; then
   find $_CONDOR_JOB_IWD -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} \;
fi
}


is_set() {
  [ "$1" != "" ]
  RSLT=$?
  return $RSLT
}

get_log_sizes() {
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

jobsub_truncate() {
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


redirect_output_start(){
    exec 7>&1
    exec >${JSB_TMP}/JOBSUB_LOG_FILE
    exec 8>&2
    exec 2>${JSB_TMP}/JOBSUB_ERR_FILE
}

redirect_output_finish(){
    exec 1>&7 7>&-
    exec 2>&8 8>&-
    jobsub_truncate ${JSB_TMP}/JOBSUB_ERR_FILE 1>&2
    jobsub_truncate ${JSB_TMP}/JOBSUB_LOG_FILE
}


normal_exit(){
    redirect_output_finish
    cleanup_condor_dirs
}

signal_exit(){
    echo "$@ "
    echo "$@ " 1>&2
    exit 255
}


trap normal_exit EXIT
trap "signal_exit received signal TERM"  TERM
trap "signal_exit received signal KILL" KILL
trap "signal_exit received signal ABRT" ABRT
trap "signal_exit received signal QUIT" QUIT
trap "signal_exit received signal ALRM" ALRM
trap "signal_exit received signal INT" INT
trap "signal_exit received signal BUS" BUS
trap "signal_exit received signal PIPE" PIPE

        """
        return lts

    def maketar_sh(self):
        cmpr = """
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
        xtrct = """
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
        poms_str = """

export NODE_NAME=`hostname`
export BOGOMIPS=`grep bogomips /proc/cpuinfo | tail -1 | cut -d ' ' -f2`
export VENDOR_ID=`grep vendor_id /proc/cpuinfo | tail -1 | cut -d ' ' -f2`
export poms_data='{"campaign_id":"'$CAMPAIGN_ID'","task_definition_id":"'$TASK_DEFINITION_ID'","task_id":"'$POMS_TASK_ID'","job_id":"'$POMS_JOB_ID'","batch_id":"'$JOBSUBJOBID'","host_site":"'$HOST_SITE'","bogomips":"'$BOGOMIPS'","node_name":"'$NODE_NAME'","vendor_id":"'$VENDOR_ID'"}'

        """
        return poms_str

    def sam_start(self):
        sam_start_str = """

yell() { echo "$0: $*" >&2; }
die() { yell "$*"; exit 111; }
try() { echo "$@"; "$@" || die "FAILED $*"; }

num_tries=0
max_tries=60
if [ "$JOBSUB_MAX_SAM_STAGE_MINUTES" != "" ]; then
    max_tries=$JOBSUB_MAX_SAM_STAGE_MINUTES
fi
try ${JSB_TMP}/ifdh.sh startProject $SAM_PROJECT $SAM_STATION $SAM_DATASET $SAM_USER $SAM_GROUP
while true; do
    STATION_STATE=${JSB_TMP}/$SAM_STATION.`date '+%s'`
    PROJECT_STATE=${JSB_TMP}/$SAM_DATASET.`date '+%s'`
    try ${JSB_TMP}/ifdh.sh dumpStation $SAM_STATION > $STATION_STATE
    grep $SAM_PROJECT $STATION_STATE > $PROJECT_STATE
    if [ "$?" != "0" ]; then
        num_tries=$(($num_tries + 1))
        if [ $num_tries -gt $max_tries ]; then
            echo "Something wrong with $SAM_PROJECT in $SAM_STATION, giving up"
            exit 111
        fi
        echo "attempt $num_tries of $max_tries: Sam Station $SAM_STATION still waiting for project $SAM_PROJECT, dataset $SAM_DATASET, sleeping 60 seconds"
        sleep 60
        continue
    fi
    TOTAL_FILES=`cat $PROJECT_STATE | sed "s/^.* contains //" | sed "s/ total files:.*$//"`
    CACHE_MIN=$TOTAL_FILES

    PROJECT_PREFETCH=`grep 'Per-project prefetched files' $STATION_STATE | sed "s/^.* files: //"`
    SCALED_PREFETCH=$[$PROJECT_PREFETCH/2]
    if [ $SCALED_PREFETCH -lt $CACHE_MIN ]; then
        CACHE_MIN=$SCALED_PREFETCH
    fi

    IN_CACHE=`cat $PROJECT_STATE | sed "s/^.*of these //" | sed "s/ in cache.*$//"`

    echo "$IN_CACHE files of $TOTAL_FILES are staged, waiting for $CACHE_MIN to stage"

    if [ $TOTAL_FILES -le 0 ]; then
        echo there are no files in $SAM_PROJECT! exiting....
        cat $STATION_STATE
        exit 1
    fi
    if [ ! -s "$PROJECT_STATE" ]; then
        echo "$SAM_PROJECT" not found in  "$SAM_STATION" ! exiting....
        cat $STATION_STATE
        exit 1
    fi
    if [ $IN_CACHE -ge $CACHE_MIN  ]; then
        echo $IN_CACHE files of $TOTAL_FILES are staged, success!
        exit 0
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
