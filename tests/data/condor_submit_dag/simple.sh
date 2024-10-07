#!/bin/sh
#

export USER="${USER:-$GRID_USER}"

# simple job wrapper
# Automatically generated by:
#          /home/${USER}/jobsub_lite/bin/jobsub_submit -e EXPERIMENT -e IFDH_DEBUG -e IFDH_VERSION -e IFDH_TOKEN_ENABLE -e IFDH_PROXY_ENABLE -e SAM_EXPERIMENT -e SAM_GROUP -e SAM_STATION -e IFDH_CP_MAXRETRIES -e VERSION -G fermilab -N 5 --no-submit --generate-email-summary --expected-lifetime=2h --disk=100MB --memory=500MB --devserver --no_submit --debug --dataset_definition=gen_cfg file://///grid/fermiapp/products/common/db/../prd/fife_utils/v3_3_2/NULL/libexec/fife_wrap --find_setups --prescript-unquote echo%20JOBSUBJOBSECTION%20is%20%24%7BJOBSUBJOBSECTION%7D --setup-unquote hypotcode%20v1_1 --setup-unquote ifdhc%20v2_6_10%2C%20ifdhc_config%20v2_6_15 --self_destruct_timer 700 --debug --getconfig --limit 1 --appvers v1_1 --metadata_extractor hypot_metadata_extractor --addoutput gen.troot --rename unique --dest /pnfs/fermilab/users/${USER}/dropbox --add_location --declare_metadata --addoutput1 hist_gen.troot --rename1 unique --dest1 /pnfs/fermilab/users/${USER}/dropbox --add_location1 --declare_metadata1 --exe hypot.exe -- -o gen.troot -c hist_gen.troot

umask 002


#
# clear out variables that sometimes bleed into containers
# causing problems.  See for example INC000001136681...
#
#
for env_var in CPATH LIBRARY_PATH LC_CTYPE
do
   eval unset $env_var
done


if grep -q release.6 /etc/system-release
then
    : tokens do not work on SL6...
    unset BEARER_TOKEN_FILE
else



export BEARER_TOKEN_FILE=$PWD/.condor_creds/fermilab_b355f5a23c.use
#export BEARER_TOKEN_FILE=$PWD/.condor_creds/fermilab.use



fi

# Set up parameter to run cvmfs_info function
CVMFS_REPO_TYPE_LIST=(opensciencegrid osgstorage)

CVMFS_REPO_LIST=fermilab



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
    JSB_OUT=$1.truncated
    if [ $JOBSUB_LOG_SIZE -gt $JOBSUB_MAX_JOBLOG_SIZE ]; then
        head -c $JOBSUB_MAX_JOBLOG_HEAD_SIZE $1 > $JSB_OUT
        echo "
jobsub:---- truncated after $JOBSUB_MAX_JOBLOG_HEAD_SIZE bytes--
" >>$JSB_OUT
        echo "
jobsub:---- resumed for last $JOBSUB_MAX_JOBLOG_TAIL_SIZE bytes--
" >>$JSB_OUT
        tail -c $JOBSUB_MAX_JOBLOG_TAIL_SIZE $1 >> $JSB_OUT
    else
        cp $1 $JSB_OUT
    fi
    cat $JSB_OUT
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


    IFDH_CP_MAXRETRIES=1 ${JSB_TMP}/ifdh.sh cp ${JSB_TMP}/JOBSUB_ERR_FILE.truncated https://fndcadoor.fnal.gov:2880/fermigrid/jobsub/jobs/2023_12_18/71a1aea7-4417-446c-920c-d3042a8f2b4b/fife_wrap2023_12_18_11225571a1aea7-4417-446c-920c-d3042a8f2b4bcluster.$CLUSTER.$PROCESS.err
    IFDH_CP_MAXRETRIES=1 ${JSB_TMP}/ifdh.sh cp ${JSB_TMP}/JOBSUB_LOG_FILE.truncated https://fndcadoor.fnal.gov:2880/fermigrid/jobsub/jobs/2023_12_18/71a1aea7-4417-446c-920c-d3042a8f2b4b/fife_wrap2023_12_18_11225571a1aea7-4417-446c-920c-d3042a8f2b4bcluster.$CLUSTER.$PROCESS.out

}


normal_exit(){
    redirect_output_finish

    # maybe don't cleanup so we can transfer files back...
    #cleanup_condor_dirs
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



setup_ifdh_env(){
#
# create ifdh.sh which runs
# ifdh in a seperate environment to
# keep it from interfering with users ifdh set up
#
cat << '_HEREDOC_' > ${JSB_TMP}/ifdh.sh
#!/bin/sh
#
which ifdh > /dev/null 2>&1
has_ifdh=$?
if [ "$has_ifdh" -ne "0" ] ; then
    unset PRODUCTS
    for setup_file in /cvmfs/fermilab.opensciencegrid.org/products/common/etc/setups /grid/fermiapp/products/common/etc/setups.sh /fnal/ups/etc/setups.sh ; do
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
chmod +x ${JSB_TMP}/ifdh.sh
}


#############################################################
# main ()                                                     #
###############################################################
touch .empty_file
# Hold and clear arg list
args="$@"
set - ""
[[ "$JOBSUB_DEBUG" ]] && set_jobsub_debug

export JSB_TMP=$_CONDOR_SCRATCH_DIR/jsb_tmp
mkdir -p $JSB_TMP
export _CONDOR_SCRATCH_DIR=$_CONDOR_SCRATCH_DIR/no_xfer
export TMP=$_CONDOR_SCRATCH_DIR
export TEMP=$_CONDOR_SCRATCH_DIR
export TMPDIR=$_CONDOR_SCRATCH_DIR
mkdir -p $_CONDOR_SCRATCH_DIR
export CONDOR_DIR_INPUT=${_CONDOR_SCRATCH_DIR}/${PROCESS}/TRANSFERRED_INPUT_FILES
mkdir -p $CONDOR_DIR_INPUT
redirect_output_start

setup_ifdh_env
export PATH="${PATH}:."

# -f files for input


# --tar_file_name for input


# -d directories for output


# ==========

  # Generic Preamble





# ==========


export JOBSUB_EXE_SCRIPT=$(ls fife_wrap 2>/dev/null)
if [ "$JOBSUB_EXE_SCRIPT" = "" ]; then
     export JOBSUB_EXE_SCRIPT=$(find . -name fife_wrap -print | head -1)
fi
chmod +x $JOBSUB_EXE_SCRIPT
${JSB_TMP}/ifdh.sh log "${USER}:$JOBSUBJOBID BEGIN EXECUTION $JOBSUB_EXE_SCRIPT   --find_setups --prescript-unquote echo%20JOBSUBJOBSECTION%20is%20%24%7BJOBSUBJOBSECTION%7D --setup-unquote hypotcode%20v1_1 --setup-unquote ifdhc%20v2_6_10%2C%20ifdhc_config%20v2_6_15 --self_destruct_timer 700 --debug --getconfig --limit 1 --appvers v1_1 --metadata_extractor hypot_metadata_extractor --addoutput gen.troot --rename unique --dest /pnfs/fermilab/users/${USER}/dropbox --add_location --declare_metadata --addoutput1 hist_gen.troot --rename1 unique --dest1 /pnfs/fermilab/users/${USER}/dropbox --add_location1 --declare_metadata1 --exe hypot.exe -- -o gen.troot -c hist_gen.troot "

export NODE_NAME=`hostname`
export BOGOMIPS=`grep bogomips /proc/cpuinfo | tail -1 | cut -d ' ' -f2`
export VENDOR_ID=`grep vendor_id /proc/cpuinfo | tail -1 | cut -d ' ' -f2`
export poms_data='{"campaign_id":"'$CAMPAIGN_ID'","task_definition_id":"'$TASK_DEFINITION_ID'","task_id":"'$POMS_TASK_ID'","job_id":"'$POMS_JOB_ID'","batch_id":"'$JOBSUBJOBID'","host_site":"'$HOST_SITE'","bogomips":"'$BOGOMIPS'","node_name":"'$NODE_NAME'","vendor_id":"'$VENDOR_ID'"}'

${JSB_TMP}/ifdh.sh log poms_data=$poms_data
echo `date` $JOBSUBJOBID BEGIN EXECUTION $JOBSUB_EXE_SCRIPT --find_setups --prescript-unquote echo%20JOBSUBJOBSECTION%20is%20%24%7BJOBSUBJOBSECTION%7D --setup-unquote hypotcode%20v1_1 --setup-unquote ifdhc%20v2_6_10%2C%20ifdhc_config%20v2_6_15 --self_destruct_timer 700 --debug --getconfig --limit 1 --appvers v1_1 --metadata_extractor hypot_metadata_extractor --addoutput gen.troot --rename unique --dest /pnfs/fermilab/users/${USER}/dropbox --add_location --declare_metadata --addoutput1 hist_gen.troot --rename1 unique --dest1 /pnfs/fermilab/users/${USER}/dropbox --add_location1 --declare_metadata1 --exe hypot.exe -- -o gen.troot -c hist_gen.troot >&2
echo `date` $JOBSUBJOBID BEGIN EXECUTION $JOBSUB_EXE_SCRIPT --find_setups --prescript-unquote echo%20JOBSUBJOBSECTION%20is%20%24%7BJOBSUBJOBSECTION%7D --setup-unquote hypotcode%20v1_1 --setup-unquote ifdhc%20v2_6_10%2C%20ifdhc_config%20v2_6_15 --self_destruct_timer 700 --debug --getconfig --limit 1 --appvers v1_1 --metadata_extractor hypot_metadata_extractor --addoutput gen.troot --rename unique --dest /pnfs/fermilab/users/${USER}/dropbox --add_location --declare_metadata --addoutput1 hist_gen.troot --rename1 unique --dest1 /pnfs/fermilab/users/${USER}/dropbox --add_location1 --declare_metadata1 --exe hypot.exe -- -o gen.troot -c hist_gen.troot

 $JOBSUB_EXE_SCRIPT --find_setups --prescript-unquote echo%20JOBSUBJOBSECTION%20is%20%24%7BJOBSUBJOBSECTION%7D --setup-unquote hypotcode%20v1_1 --setup-unquote ifdhc%20v2_6_10%2C%20ifdhc_config%20v2_6_15 --self_destruct_timer 700 --debug --getconfig --limit 1 --appvers v1_1 --metadata_extractor hypot_metadata_extractor --addoutput gen.troot --rename unique --dest /pnfs/fermilab/users/${USER}/dropbox --add_location --declare_metadata --addoutput1 hist_gen.troot --rename1 unique --dest1 /pnfs/fermilab/users/${USER}/dropbox --add_location1 --declare_metadata1 --exe hypot.exe -- -o gen.troot -c hist_gen.troot
JOB_RET_STATUS=$?

# copy out job log file


# copy out -d directories


# log cvmfs info, in case of problems
# on job failure: everything after second-to-last "switched to catalog revision x"
# on job success: last 'catalog revision n' line
cvmfs_info() {
    cvmfs_repo=${1}
    cvmfs_repo_type=${2}
    if test -d /cvmfs/${cvmfs_repo}.${cvmfs_repo_type}.org/;
    then
        echo "cvmfs info repo: ${cvmfs_repo}.${cvmfs_repo_type}.org" >&2
    else
        echo "cvmfs info repo: ${cvmfs_repo}.${cvmfs_repo_type}.org not present" >&2
        return
    fi
    # pick filter based on job status, whether we have multiple "switched to catalog revision" lines
    if [ $JOB_RET_STATUS = 0 ]
    then
        filter="grep to.catalog.revision | tail -1"
    else
        dummyline="__dummy__to_catalog_revision"
        second_latest_rev_re=$( (echo "$dummyline"; attr -g logbuffer /cvmfs/${cvmfs_repo}.${cvmfs_repo_type}.org/) |
                               grep to.catalog.revision |
                               tail -2 | head -1 |
                               sed -e 's/[][\/\\]/\\&/g'  # backslash escape square brackets and slashes
                           )

        if [ "$second_latest_rev_re" = "$dummyline" ]
        then
            # there were zero or one "switched to catalog revision x" lines, send them all
            filter=cat
        else
            # delete everything up to that second latest one
            filter="sed -e '1,/$second_latest_rev_re/d'"
        fi
    fi

    # now log filtered messages to ifdh, and into stderr

    attr -g logbuffer /cvmfs/${cvmfs_repo}.${cvmfs_repo_type}.org/ |
        grep -v '^$' |
        eval "$filter" |
        while read line
        do
            ${JSB_TMP}/ifdh.sh log "$JOBSUBJOBID cvmfs: $line"
            echo $line >&2
        done
}

for CVMFS_REPO in ${CVMFS_REPO_LIST[@]}
do
    for CVMFS_REPO_TYPE in ${CVMFS_REPO_TYPE_LIST[@]}
    do
        cvmfs_info ${CVMFS_REPO} ${CVMFS_REPO_TYPE}
    done
done

echo `date` $JOBSUB_EXE_SCRIPT COMPLETED with exit status $JOB_RET_STATUS
echo `date` $JOBSUB_EXE_SCRIPT COMPLETED with exit status $JOB_RET_STATUS 1>&2
${JSB_TMP}/ifdh.sh log "$JOBSUBJOBID ${USER}:fife_wrap COMPLETED with return code $JOB_RET_STATUS"

exit $JOB_RET_STATUS
