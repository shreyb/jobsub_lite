#!/bin/sh
#

# simple job wrapper
# Automatically generated by:
#          {{jobsub_command}}

umask 002

{% if not no_env_cleanup %}
#
# clear out variables that sometimes bleed into containers
# causing problems.  See for example INC000001136681...
# {% if not_clean_env_vars %}NOT clearing {{not_clean_env_vars}} because of -e arguments {% endif %}
#
for env_var in {{clean_env_vars}}
do
   eval unset $env_var
done
{% endif %}

if grep -q release.6 /etc/system-release
then
    : tokens do not work on SL6...
    unset BEARER_TOKEN_FILE
else

{% if token is defined and token %}
{% if role is defined and role and role != 'Analysis' %}
export BEARER_TOKEN_FILE=$PWD/.condor_creds/{{group}}_{{role | lower}}_{{oauth_handle}}.use
#export BEARER_TOKEN_FILE=$PWD/.condor_creds/{{group}}_{{role | lower}}.use
{% else %}
export BEARER_TOKEN_FILE=$PWD/.condor_creds/{{group}}_{{oauth_handle}}.use
#export BEARER_TOKEN_FILE=$PWD/.condor_creds/{{group}}.use
{% endif %}
{% endif %}

fi

# Set up parameters used by cvmfs_info function
CVMFS_REPO_TYPE_LIST=(opensciencegrid osgstorage)
CVMFS_REPO_LIST=({{group}}
{%- if group in ('dune','sbnd','icarus','lariat','argoneut') %} larsoft{% endif -%}
{%- if group in ('sbnd','icarus') %} sbn{% endif -%}
)

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
    {%if outurl%}
    {% set filebase %}{{executable|basename}}{{datetime}}{{uuid}}cluster.$CLUSTER.$PROCESS{% endset %}
    IFDH_CP_MAXRETRIES=1 ${JSB_TMP}/ifdh.sh cp ${JSB_TMP}/JOBSUB_ERR_FILE.truncated {{outurl}}/{{filebase}}.err
    IFDH_CP_MAXRETRIES=1 ${JSB_TMP}/ifdh.sh cp ${JSB_TMP}/JOBSUB_LOG_FILE.truncated {{outurl}}/{{filebase}}.out
    {%endif%}
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
    . /cvmfs/fermilab.opensciencegrid.org/packages/common/setup-env.sh
    sos=$(spack arch --operating-system)
    spack env activate ifdh_env_${sos}_${IFDH_VERSION:-current} ||
      echo Falling back to current ifdhc for this operation >&2 &&
      spack env activate ifdh_env_${sos}_current
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
{%for fname in input_file%}
  {%if fname[:6] == "/cvmfs" and "fifeuser" in fname%}
    # RCDS unpacked tarfile
    # Save tfname into a list in case we couldn't get the exact path, like if user skipped the RCDS upload check
    fnamelist=({{fname}})

    # Given 40 tries, with a sleep of 30 seconds, we retry for a maximum of around 20 minutes PER item in fnamelist
    num_tries=0
    max_tries=40
    slp=30

    # wait for RCDS file to show up.  We check all possible locations each try
    num_tries=0
    while [ ${num_tries} -lt ${max_tries} ]; do
      num_tries=$(($num_tries + 1))
      fnamelist=( `shuf -e "${fnamelist[@]}"` ) # Shuffle our list
      for candidate_fname in ${fnamelist[@]}; do
        echo "Looking for file ${candidate_fname} on RCDS.  Try ${num_tries} of ${max_tries}"
        if test -f "${candidate_fname}"; then
            echo "Found file ${candidate_fname} on RCDS.  Copying in."
            ${JSB_TMP}/ifdh.sh cp -D ${candidate_fname} ${CONDOR_DIR_INPUT}
            break 2 # Break out of both candidate_fname and retry loop
        fi
      done
      if [[ $num_tries -eq $max_tries ]]; then
        echo "Max retries ${num_tries} exceeded to find ${candidate_fname} on RCDS.  Exiting now."
        exit 1 # Fail the job right here
      fi
      sleep $slp
    done
  {%else%}
    ${JSB_TMP}/ifdh.sh cp -D {{fname}} ${CONDOR_DIR_INPUT}
    chmod u+x ${CONDOR_DIR_INPUT}/{{fname|basename}}
  {%endif%}
{%endfor%}

# --tar_file_name for input
{%for tfname in tar_file_name%}
  {%if tfname[:6] == "/cvmfs" and tfname[-7:] != ".tar.gz" %}
    # RCDS unpacked tarfile
    # Save tfname into a list in case we couldn't get the exact path, like if user skipped the RCDS upload check
    tfnamelist=({{tfname}})

    # Given 40 tries, with a sleep of 30 seconds, we retry for a maximum of around 20 minutes PER item in tfnamelist
    num_tries=0
    max_tries=40
    slp=30

    # wait for tarfile to show up
    while [[ ${num_tries} -lt ${max_tries} ]]; do
      num_tries=$(($num_tries + 1))
      tfnamelist=( `shuf -e "${tfnamelist[@]}"` ) # Shuffle our list
      for candidate_tfname in ${tfnamelist[@]}; do
        echo "Looking for directory ${candidate_tfname} on RCDS.  Try ${num_tries} of ${max_tries}"
        if test -d "${candidate_tfname}" ; then
          # found the tarfile.  Set the environment variables
          echo "Found file ${candidate_tfname} on RCDS.  Setting environment variables and links in job."
          {%if loop.first%}
            INPUT_TAR_DIR_LOCAL=${candidate_tfname}
            export INPUT_TAR_DIR_LOCAL
            # Note: this filename doesn't exist, but if you take dirname
            #       of it you find the contents
            INPUT_TAR_FILE=${candidate_tfname}/{{tar_file_orig_basenames[loop.index0]}}.tar
            export INPUT_TAR_FILE
            ln -s ${candidate_tfname} ${CONDOR_DIR_INPUT}/{{tar_file_orig_basenames[loop.index0]}}
            break 2 # Break out of both candidate_tfname and retry loop
          {%else%}
            INPUT_TAR_DIR_LOCAL_{{loop.index0}}=${candidate_tfname}
            export INPUT_TAR_DIR_LOCAL_{{loop.index0}}
            # Note: this filename doesn't exist, but if you take dirname
            #       of it you find the contents
            INPUT_TAR_FILE_{{loop.index0}}=${candidate_tfname}/{{tar_file_orig_basenames[loop.index0]}}.tar
            export INPUT_TAR_FILE_{{loop.index0}}
            ln -s ${candidate_tfname} ${CONDOR_DIR_INPUT}/{{tar_file_orig_basenames[loop.index0]}}
            break 2 # Break out of both candidate_tfname and retry loop
          {%endif%}
        fi
      done
      if [[ $num_tries -eq $max_tries ]] ; then
        echo "Max retries ${num_tries} exceeded to find ${candidate_tfname}.  Exiting."
        exit 1 # Fail the job right here
      fi
      sleep $slp
    done
  {%else%}
    # tarfile to transfer and unpack
    mkdir .unwind_{{loop.index0}}
    {%set tflocal = '.unwind_%d/%s' % (loop.index0, tfname|basename) %}
    ${JSB_TMP}/ifdh.sh cp {{tfname}} {{tflocal}}
    tar --directory .unwind_{{loop.index0}} -xjvf {{tflocal}}
    {%if loop.first%}
      INPUT_TAR_DIR_LOCAL=`pwd`/.unwind_{{loop.index0}}
      export INPUT_TAR_DIR_LOCAL
      INPUT_TAR_FILE={{tflocal}}
      export INPUT_TAR_FILE
      ln -s $INPUT_TAR_FILE ${CONDOR_DIR_INPUT}/{{tar_file_orig_basenames[loop.index0]}}
    {%else%}
      INPUT_TAR_DIR_LOCAL_{{loop.index0}}=`pwd`/.unwind_{{loop.index0}}
      export INPUT_TAR_DIR_LOCAL_{{loop.index0}}
      INPUT_TAR_FILE_{{loop.index0}}={{tflocal}}
      export INPUT_TAR_FILE_{{loop.index0}}
      ln -s $INPUT_TAR_FILE_{{loop.index0}} ${CONDOR_DIR_INPUT}/{{tar_file_orig_basenames[loop.index0]}}
    {%endif%}
  {%endif%}
{%endfor%}

# -d directories for output
{%for pair in d%}
export CONDOR_DIR_{{pair[0]}}=`pwd`/out_{{pair[0]}}
mkdir $CONDOR_DIR_{{pair[0]}}
{%endfor%}

# ==========
{%if group == 'minerva' %}
  # Minerva preamble
  {%if i%}
    source {{i}}/setup.sh -c {{cmtconfig}}
    {%if t%}
      pushd {{t}}/cmt
      cmt config
      source setup.sh
      popd
   {%endif%}
 {%endif%}

{%else%}
  # Generic Preamble
  {%if i%}
    source {{i}}/setup.sh
  {%endif%}
  {%if t%}
    source {{t}}/setup.sh
  {%endif%}
  {%if r%}
    setup  {{group}}{%if group=="dune"%}tpc{%else%}code{%endif%} {{r}}
  {%endif%}

{%endif%}
# ==========


export JOBSUB_EXE_SCRIPT=$(ls {{executable|basename}} 2>/dev/null)
if [ "$JOBSUB_EXE_SCRIPT" = "" ]; then
     export JOBSUB_EXE_SCRIPT=$(find . -name {{executable|basename}} -print | head -1)
fi
chmod +x $JOBSUB_EXE_SCRIPT
${JSB_TMP}/ifdh.sh log "$USER:$JOBSUBJOBID BEGIN EXECUTION $JOBSUB_EXE_SCRIPT   {{exe_arguments|join(" ")}} "

export NODE_NAME=`hostname`
export BOGOMIPS=`grep bogomips /proc/cpuinfo | tail -1 | cut -d ' ' -f2`
export VENDOR_ID=`grep vendor_id /proc/cpuinfo | tail -1 | cut -d ' ' -f2`
export poms_data='{"campaign_id":"'$CAMPAIGN_ID'","task_definition_id":"'$TASK_DEFINITION_ID'","task_id":"'$POMS_TASK_ID'","job_id":"'$POMS_JOB_ID'","batch_id":"'$JOBSUBJOBID'","host_site":"'$HOST_SITE'","bogomips":"'$BOGOMIPS'","node_name":"'$NODE_NAME'","vendor_id":"'$VENDOR_ID'"}'

${JSB_TMP}/ifdh.sh log poms_data=$poms_data
echo `date` $JOBSUBJOBID BEGIN EXECUTION $JOBSUB_EXE_SCRIPT {{exe_arguments|join(" ")}} >&2
echo `date` $JOBSUBJOBID BEGIN EXECUTION $JOBSUB_EXE_SCRIPT {{exe_arguments|join(" ")}}

{%if timeout is defined and timeout %} timeout {{timeout}} {%endif%} $JOBSUB_EXE_SCRIPT {{exe_arguments|join(" ")}} {%if log_file is defined and log_file %}> _joblogfile 2>&1 {% endif %}
JOB_RET_STATUS=$?

# copy out job log file
{%if log_file is defined and log_file %}
${JSB_TMP}/ifdh.sh cp _joblogfile {{log_file}}
{%endif%}

# copy out -d directories
{%for pair in d%}
${JSB_TMP}/ifdh.sh cp -D $CONDOR_DIR_{{pair[0]}}/* {{pair[1]}}
{%endfor%}

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
            IFDH_DEBUG=0 ${JSB_TMP}/ifdh.sh log "$JOBSUBJOBID cvmfs: $line"
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
${JSB_TMP}/ifdh.sh log "$JOBSUBJOBID {{user}}:{{executable|basename}} COMPLETED with return code $JOB_RET_STATUS"

exit $JOB_RET_STATUS
