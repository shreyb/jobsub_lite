#!/bin/bash 
if [ "$2" != "" ]; then
   SLEEP_LENGTH=$2
else
   SLEEP_LENGTH=180
fi

if [ -e "$3" ]; then
   source $3
fi

rm -f $HOME/stop_load_test
rm -f *_sub.log 
export GROUP=nova
./repeat_submit_with_role.sh $1 &
nova_pid=$!
export GROUP=minos
./repeat_submit_with_role.sh $1 &
minos_pid=$!
export GROUP=minerva
./repeat_submit_with_role.sh $1 &
minerva_pid=$!
export GROUP=mu2e
./repeat_submit_with_role.sh $1 &
mu2e_pid=$!
./stop_test_after_sleep.sh $SLEEP_LENGTH &

echo "pids:  nova $nova_pid  minos $minos_pid  minerva $minerva_pid  mu2e $mu2e_pid "

wait $nova_pid $minos_pid $minerva_pid $mu2e_pid
stat=$?
echo $0 exiting with status $stat
exit $stat
