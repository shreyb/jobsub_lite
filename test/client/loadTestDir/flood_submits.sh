#!/bin/sh 

rm -f $HOME/stop_load_test
rm -f *_sub.log 
export GROUP=nova
./repeat_submit_with_role.sh $1 &
export GROUP=minos
./repeat_submit_with_role.sh $1 &
export GROUP=minerva
./repeat_submit_with_role.sh $1 &
export GROUP=lbne
./repeat_submit_with_role.sh $1 &
