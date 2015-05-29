#!/bin/sh 

rm -f $HOME/stop_load_test
rm -f *_dag.log 
export GROUP=nova
./repeat_dag_submit_with_role.sh $1 &
export GROUP=minos
./repeat_dag_submit_with_role.sh $1 &
export GROUP=minerva
./repeat_dag_submit_with_role.sh $1 &
export GROUP=lbne
./repeat_dag_submit_with_role.sh $1 &
