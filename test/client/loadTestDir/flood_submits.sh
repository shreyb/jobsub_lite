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
export GROUP=lbne
./repeat_submit_with_role.sh $1 &
lbne_pid=$!
./stop_test_after_sleep.sh $SLEEP_LENGTH &

echo "pids:  nova $nova_pid  minos $minos_pid  minerva $minerva_pid  lbne $lbne_pid "

#wait $nova_pid
#nova_status=$?
#wait $minos_pid
#minos_status=$?
#wait $minerva_pid
#minerva_status=$?
#wait $lbne_pid
#lbne_status=$?

#echo "status:  nova $nova_status  minos $minos_status  minerva $minerva_status  lbne $lbne_status "
#! (( $nova_status || $minos_status || $minerva_status || $lbne_status ))
wait
stat=$?
echo $0 exiting with status $stat
exit $stat
