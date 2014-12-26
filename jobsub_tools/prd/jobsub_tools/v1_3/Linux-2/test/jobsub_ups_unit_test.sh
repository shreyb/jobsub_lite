#!/bin/bash

source $UPS_DIR/test/unittest.bash

test_setup() {
   testdir=/tmp/t$$
   testout=/tmp/test_case_out_$$
   mkdir -p $testdir/tmp
   mkdir -p $testdir/exec
   export CONDOR_TMP=$testdir/tmp
   export CONDOR_EXEC=$testdir/exec
}

test_teardown() {
   if [ "$SAVE_TEST_OUTPUT" = "" ]; then
       rm -rf $testdir
       rm -rf $testout
   fi
}

print_cmd_file() {
   echo command file: $file
   return 0
   # print file, so error report is helpful if it fails
   echo "cmd file:"
   echo "----"
   cat $file
   echo
   echo "----"
}

test_lines() {
   file=`jobsub -n  -lines="foo" -lines="bar" /usr/bin/printenv`

   print_cmd_file

   # succeeds if foo and bar are in the file
   grep foo $file /dev/null && grep bar $file /dev/null
}


test_append_requirements1() {
   #SUBMIT_HOST=gpsn01.fnal.gov
   #JOBSUB_INI_FILE=${JOBSUB_TOOLS_DIR}/bin/jobsub.ini
   file=`jobsub -n -e SUBMIT_HOST  --append_condor_requirements=foo -c bar /usr/bin/printenv`

   print_cmd_file
   # succeeds if foo and bar are in the file, and in the requirements line
   grep 'requirements.*foo' $file /dev/null && grep 'requirements.*bar' $file /dev/null
}

test_append_requirements2() {
   #SUBMIT_HOST=gpsn01.fnal.gov
   #JOBSUB_INI_FILE=${JOBSUB_TOOLS_DIR}/bin/jobsub.ini
   file=`jobsub -n -e SUBMIT_HOST  -g --append_condor_requirements=foo -c bar /usr/bin/printenv`

   print_cmd_file
   # succeeds if foo and bar are in the file, and in the requirements line
   grep 'requirements.*foo' $file /dev/null && grep 'requirements.*bar' $file /dev/null
}


test_append_requirements3() {
   #SUBMIT_HOST=not.gpsn01.fnal.gov
   file=`jobsub -e SUBMIT_HOST -n  --append_condor_requirements=foo -c bar /usr/bin/printenv`

   print_cmd_file
   # succeeds if foo and bar are in the file, and in the requirements line
   grep 'requirements.*foo' $file /dev/null && grep 'requirements.*bar' $file /dev/null
}

test_append_requirements4() {
   #SUBMIT_HOST=not.gpsn01.fnal.gov
   file=`jobsub -e SUBMIT_HOST -n -g  --append_condor_requirements=foo -c bar /usr/bin/printenv`

   print_cmd_file
   # succeeds if foo and bar are in the file, and in the requirements line
   grep 'requirements.*foo' $file /dev/null && grep 'requirements.*bar' $file /dev/null
}

test_append_accounting_group() {
   SUBMIT_HOST=gpsn01.fnal.gov
   JOBSUB_INI_FILE=${JOBSUB_TOOLS_DIR}/bin/jobsub.ini
   file=`jobsub -n -g -l '+AccountingGroup = "group_highprio.minervapro"' /usr/bin/printenv`
   print_cmd_file

   # succeeds if +AccountingGroup = "group_highprio.minervapro" appears last of all +AccountingGroup s
   grep 'AccountingGroup' $file > ${file}.1
   tail -1 ${file}.1 > ${file}.2
   grep 'group_highprio.minervapro' ${file}.2 
}

test_OS() {
   #SUBMIT_HOST=gpsn01.fnal.gov
   #JOBSUB_INI_FILE=${JOBSUB_TOOLS_DIR}/bin/jobsub.ini
   file=`jobsub -n -g --OS=foo,bar /usr/bin/printenv`
   print_cmd_file

   # succeeds if foo and bar are in the DesiredOS line
   grep '+DesiredOS *= *"foo,bar"' $file /dev/null 
}  

test_drain() {
   #SUBMIT_HOST=gpsn01.fnal.gov
   #JOBSUB_INI_FILE=${JOBSUB_TOOLS_DIR}/bin/jobsub.ini
   file=`jobsub -n -g --drain  /usr/bin/printenv`
   print_cmd_file

   # succeeds if Drain = True in jdf
   grep '+Drain = True' $file /dev/null 
}  

test_mem_disk_cpu_1() {
   #SUBMIT_HOST=gpsn01.fnal.gov
   #JOBSUB_INI_FILE=${JOBSUB_TOOLS_DIR}/bin/jobsub.ini
   file=`jobsub -n -g --cpu 3 --disk 40980000 --memory 9999  /usr/bin/printenv`
   print_cmd_file

   # succeeds if foo and bar are in the DesiredOS line
   grep 'request_cpu = 3' $file /dev/null && grep 'request_disk = 40980000' $file /dev/null && grep 'request_memory = 9999' $file /dev/null 
}  

test_mem_disk_cpu_2() {
   #SUBMIT_HOST=fifebatch1.fnal.gov
   #JOBSUB_INI_FILE=${JOBSUB_TOOLS_DIR}/bin/jobsub.ini
   file=`jobsub -n -g --cpu 3 --disk 40980000 --memory 9999  /usr/bin/printenv`
   print_cmd_file

   # succeeds if foo and bar are in the DesiredOS line
   grep 'request_cpu = 3' $file /dev/null && grep 'request_disk = 40980000' $file /dev/null && grep 'request_memory = 9999' $file /dev/null 
}  



testsuite setups_suite	\
    -s test_setup 	\
    -t test_teardown	\
    test_lines		\
    test_append_requirements1 \
    test_append_requirements2 \
    test_append_requirements3 \
    test_append_requirements4 \
    test_append_accounting_group \
    test_OS \
    test_drain \
    test_mem_disk_cpu_1 \
    test_mem_disk_cpu_2 \
   

setups_suite "$@"
