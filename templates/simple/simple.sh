#!/bin/sh
#
umask 002
# {{file}}_wrap.sh
# Automatically generated by: 
#          {{jobsub_command}}

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
{%for fname in input_file%}
${JSB_TMP}/ifdh.sh cp -D {{fname}} .
{%endfor%}

# --tar_file_name for input
{%for tfname in tar_file_name%}
  {%if tfname[:6] == "/cvmfs" and tfname[-7:] != ".tar.gz" %}
    # RCDS unpacked tarfile
    {%if loop.first%}
      INPUT_TAR_FILE={{tfname}}
      export INPUT_TAR_FILE
    {%else%}
      INPUT_TAR_FILE_{{loop.index0}}={{tfname}}
      export INPUT_TAR_FILE_{{loop.index0}}
    {%endif%}
  {%else%}
    # tarfile to transfer and unpack
    mkdir .unwind_{{loop.index0}}
    {%set tflocal = '.unwind_%d/%s' % (loop.index0, tfname|basename) %}
    ${JSB_TMP}/ifdh.sh cp {{tfname}} {{tflocal}}
    tar --directory .unwind_{{loop.index0}} -xzvf {{tflocal}} 
    {%if loop.first%}
      INPUT_TAR_FILE=`pwd`/.unwind_{{loop.index0}}
      export INPUT_TAR_FILE
    {%else%}
      INPUT_TAR_FILE_{{loop.index0}}=`pwd`/.unwind_{{loop.index0}}
      export INPUT_TAR_FILE_{{loop.index0}}
    {%endif%}
  {%endif%}
{%endfor%}

# -d directories for output
{%for pair in d%}
export JOBSUB_OUT_{{pair[0]}}=out_{{pair[0]}}
mkdir $JOBSUB_OUT_{{pair[0]}}
{%endfor%}

# ==========
{%if group == 'minos' %}
    #Minos Preamble
    if [ -d "/grid/fermiapp/minos/" ]; then
        export MINOS_ENSTORE=/grid/fermiapp/minos/enstore
        source /grid/fermiapp/minos/enstore/setup_aliases.sh
        export PATH="/grid/fermiapp/minos/enstore:${PATH}"
        export MINOS_GRIDDB=/grid/fermiapp/minos/griddb
        export PATH="/grid/fermiapp/minos/griddb:${PATH}"
      {%if r %}
        export ENV_TSQL_URL=`/grid/fermiapp/minos/griddb/choose_db_server`
        echo Setting database URL to $ENV_TSQL_URL
        export MINOS_SETUP_DIR=/grid/fermiapp/minos/minossoft/setup
        #unset SETUP_UPS SETUPS_DIR
        #. /grid/fermiapp/nova/products/db/.upsfiles/configure/v4_7_4a_Linux+2_/setups.sh

        setup_minos()
             {
               . $MINOS_SETUP_DIR/setup_minossoft_FNALU.sh $*
             }
        setup_minos -r {{r}}
      {%endif%}
      {%if t%}
        if [ -d "{{t}}" ] then;
                    echo Running 'srt_setup -a' in `relpathto {{t}}`
            here=`/bin/pwd`
            cd `relpathto {{t}}`
            srt_setup -a
            cd $here
        fi
      {%endif%}
    fi

{%elif group == 'nova' %}
  # NOvA preamble
  {%if r%}
    source /grid/fermiapp/nova/novaart/novasvn/srt/srt.sh
    export EXTERNALS=/nusoft/app/externals
    source $SRT_DIST/setup/setup_novasoft.sh -r {{r}}
  {%endif%} 
  {%if t%}
    echo "Running 'srt_setup -a' in  %s"
    here=`/bin/pwd`
    cd {{t}} 
    srt_setup -a
    cd $here 
  {%endif%} 


{%elif group == 'minerva' %}
  # Minerva preamble
  {%if i%}
    source {{i}}/setup.sh -c {{r}} {{cmtconfig}}
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


export JOBSUB_EXE_SCRIPT=$(ls {{full_executable}} 2>/dev/null)
if [ "$JOBSUB_EXE_SCRIPT" = "" ]; then 
     export JOBSUB_EXE_SCRIPT=$(find . -name {{executable|basename}} -print | head -1)
fi
chmod +x $JOBSUB_EXE_SCRIPT
${JSB_TMP}/ifdh.sh log "mengel:$JOBSUBJOBID BEGIN EXECUTION $JOBSUB_EXE_SCRIPT   {{exe_arguments|join(" ")}} "

export NODE_NAME=`hostname`
export BOGOMIPS=`grep bogomips /proc/cpuinfo | tail -1 | cut -d ' ' -f2`
export VENDOR_ID=`grep vendor_id /proc/cpuinfo | tail -1 | cut -d ' ' -f2`
export poms_data='{"campaign_id":"'$CAMPAIGN_ID'","task_definition_id":"'$TASK_DEFINITION_ID'","task_id":"'$POMS_TASK_ID'","job_id":"'$POMS_JOB_ID'","batch_id":"'$JOBSUBJOBID'","host_site":"'$HOST_SITE'","bogomips":"'$BOGOMIPS'","node_name":"'$NODE_NAME'","vendor_id":"'$VENDOR_ID'"}'

${JSB_TMP}/ifdh.sh log poms_data=$poms_data
echo `date` $JOBSUBJOBID BEGIN EXECUTION $JOBSUB_EXE_SCRIPT {{exe_arguments|join(" ")}} >&2 
echo `date` $JOBSUBJOBID BEGIN EXECUTION $JOBSUB_EXE_SCRIPT {{exe_arguments|join(" ")}}

{%if timeout%} timeout {{timeout}} {%endif%} $JOBSUB_EXE_SCRIPT {{exe_arguments|join(" ")}} 
JOB_RET_STATUS=$?

# copy out -d directories
{%for pair in d%}
${JSB_TMP}/ifdh.sh cp -D $JOBSUB_OUT_{{pair[0]}}/* {{pair[1]}}
{%endfor%}

echo `date` $JOBSUB_EXE_SCRIPT COMPLETED with exit status $JOB_RET_STATUS
echo `date` $JOBSUB_EXE_SCRIPT COMPLETED with exit status $JOB_RET_STATUS 1>&2
${JSB_TMP}/ifdh.sh log "$JOBSUBJOBID {{user}}:{{executable|basename}} COMPLETED with return code $JOB_RET_STATUS" 
exit $JOB_RET_STATUS