#!/bin/sh

function define_if_needed {
        eval var=\$$1
        if [ "$var" = "" ]; then
                export $1=$2
        fi
}

define_if_needed SAM_STATION cdf-caf
define_if_needed SAM_GROUP cdf
define_if_needed SAM_USER `whoami`
#define_if_needed SAM_DATASET `whoami`_test_zzz_10
define_if_needed SAM_PROJECT1 `whoami`_test_project_1_`date +%s`
define_if_needed SAM_PROJECT2 `whoami`_test_project_2_`date +%s`
define_if_needed SAM_PROJECT3 `whoami`_test_project_3_`date +%s`
define_if_needed SAM_PROJECT4 `whoami`_test_project_4_`date +%s`
define_if_needed SAM_PROJECT5 `whoami`_test_project_5_`date +%s`
define_if_needed IFDH_BASE_URI http://samweb.fnal.gov:8480/sam/cdf/api

kx509 -o /tmp/jobsub_x509up_u${UID}_cdf

cd ..
source ./setup_env.sh
cd -
export DFN_CNT=`wc -l ./test_definition_list| awk '{print $1}'`
export SAM_DATASET=`head -$(($RANDOM%$DFN_CNT+1)) test_definition_list | tail -1`
echo $SERVER_SPEC | grep fifebatch >/dev/null 2>&1
IS_FIFEBATCH="$?"
if [ "$IS_FIFEBATCH" = "0" ]; then
    RESOURCE_PROVIDES="-g --OS=SL6 --resource-provides=usage_model=DEDICATED,OPPORTUNISTIC"
fi
#if [ 1 = 0 ]; then
gCMD="$EXEPATH/jobsub_submit $SUBMIT_FLAGS \
    --debug
    -e SAM_STATION \
    -e SAM_GROUP \
    -e SAM_USER \
    -e SAM_DATASET \
    -e SAM_PROJECT1 \
    -e IFDH_BASE_URI \
    -G cdf $RESOURCE_PROVIDES \
    -N 3 --generate-email-summary \
    --mail_on_error --maxParallelSec 5 \
    --dataset_definition=$SAM_DATASET \
    --project_name=$SAM_PROJECT1 \
    $SERVER_SPEC \
    --tarFile=dropbox://input.tgz \
     file://testSAM.sh $ foo bar baz"

echo $gCMD

$gCMD

T0=$?

export SAM_DATASET=`head -$(($RANDOM%$DFN_CNT+1)) test_definition_list | tail -1`
gCMD2="$EXEPATH/jobsub_submit $SUBMIT_FLAGS \
    --debug
    -e SAM_STATION \
    -e SAM_USER \
    -e SAM_DATASET \
    -e SAM_PROJECT2 \
    -e IFDH_BASE_URI \
    -G cdf $RESOURCE_PROVIDES \
    -N 3 --generate-email-summary \
    --mail_on_error --maxParallelSec 5 \
    --dataset_definition=$SAM_DATASET \
    --project_name=$SAM_PROJECT2 \
    $SERVER_SPEC \
    --tarFile dropbox://input2.tgz \
    file://some_subdir/testSAM.sh $ foo bar baz"

echo $gCMD2

$gCMD2

T1=$?
#fi #if 1=0

export SAM_DATASET=`head -$(($RANDOM%$DFN_CNT+1)) test_definition_list | tail -1`
gCMD3="$EXEPATH/jobsub_submit $SUBMIT_FLAGS \
    --debug
    -e SAM_STATION \
    -e SAM_USER \
    -e SAM_DATASET \
    -e SAM_PROJECT3 \
    -e IFDH_BASE_URI \
    -G cdf $RESOURCE_PROVIDES \
    -N 3 --generate-email-summary \
    --mail_on_error --maxParallelSec 5 \
    --dataset_definition=$SAM_DATASET \
    --project_name=$SAM_PROJECT3 \
    $SERVER_SPEC \
    --tarFile dropbox://input2.tgz \
    some_subdir/testSAM.sh $ foo bar baz"

echo $gCMD3

$gCMD3

T2=$?

export SAM_DATASET=`head -$(($RANDOM%$DFN_CNT+1)) test_definition_list | tail -1`
gCMD="$EXEPATH/jobsub_submit $SUBMIT_FLAGS \
    --debug
    -e SAM_STATION \
    -e SAM_USER \
    -e SAM_DATASET \
    -e SAM_PROJECT3 \
    -e IFDH_BASE_URI \
    -G cdf $RESOURCE_PROVIDES \
    -N 3 --generate-email-summary \
    --mail_on_error --maxParallelSec 5 \
    --dataset_definition=$SAM_DATASET \
    --project_name=$SAM_PROJECT3 \
    $SERVER_SPEC \
    --tarFile=dropbox://input.tgz \
     ./testSAM.sh $ foo bar baz"
echo ======================================================
echo $gCMD
echo ======================================================

$gCMD

T3=$?
echo exit status of last command $T3

gCMD="$EXEPATH/jobsub_submit $SUBMIT_FLAGS \
    --debug
    -e IFDH_BASE_URI \
    -G cdf $RESOURCE_PROVIDES \
    -N 3 --generate-email-summary \
    --mail_on_error --maxParallelSec 5 \
    $SERVER_SPEC \
    --tarFile=dropbox://input3.tgz \
     some_subdir/testNoSAM.sh $ foo bar baz"
echo ======================================================
echo $gCMD
echo ======================================================

$gCMD

T4=$?
echo exit status of last command $T4

export SAM_DATASET=`head -$(($RANDOM%$DFN_CNT+1)) test_definition_list | tail -1`
gCMD="$EXEPATH/jobsub_submit $SUBMIT_FLAGS \
    --debug
    -e SAM_STATION \
    -e SAM_GROUP \
    -e SAM_USER \
    -e SAM_DATASET \
    -e SAM_PROJECT4 \
    -e IFDH_BASE_URI \
    -G cdf $RESOURCE_PROVIDES \
    --start 3 --end 5 --generate-email-summary \
    --mail_on_error --maxParallelSec 5 \
    --dataset_definition=$SAM_DATASET \
    --project_name=$SAM_PROJECT4 \
    $SERVER_SPEC \
    --tarFile=dropbox://input.tgz \
     testSAM.sh $ foo bar baz"
echo ======================================================
echo $gCMD
echo ======================================================

$gCMD
T5=$?
echo exit status of last command $T5


tar cvzf input4.tgz I_will_fail.sh 

gCMD="$EXEPATH/jobsub_submit $SUBMIT_FLAGS \
    --debug
    -e SAM_STATION \
    -e SAM_GROUP \
    -e SAM_USER \
    -e SAM_DATASET \
    -e SAM_PROJECT5 \
    -e IFDH_BASE_URI \
    -G cdf $RESOURCE_PROVIDES \
    -N 3   \
    --mail_on_error --maxParallelSec 5 \
    --dataset_definition=$SAM_DATASET \
    --project_name=$SAM_PROJECT5 \
    $SERVER_SPEC \
    --tarFile=dropbox://input4.tgz \
     I_will_fail.sh $ foo bar baz"
echo ======================================================
echo $gCMD
echo ======================================================

$gCMD
T6=$?
echo exit status of last command $T6


! (( $T0 || $T1 || $T2 || $T3  || $T4 || $T5 || $T6 ))

TF=$?
exit $TF
