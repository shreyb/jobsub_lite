#!/bin/sh

source ./setup_env.sh

#test list of $COMMANDS with $FLAGS for exit status $code ($1)
function test_for_return_vals() {
    code=$1
    if [ "$code" = "" ]; then
        code=2
    fi
    for CMD in $COMMANDS; do
        CMD_="$EXEPATH/$CMD $FLAGS"
        echo testing return value of: $CMD_
        $CMD_ > /dev/null 2>&1
        STAT=$?
        if  [ "$STAT" -ne $code ]; then
            echo "FAIL" 
            echo "FAIL $CMD_ returned $STAT, expected $code" 
            echo "FAIL" 
            exit 1
        fi
    done
}

COMMANDS="jobsub_fetchlog jobsub_history jobsub_hold jobsub_q jobsub_release jobsub_rm  jobsub_submit jobsub_submit_dag"
FLAGS=" -G nova -G nova"
test_for_return_vals 2

COMMANDS="jobsub_status"
FLAGS=" -G nova -G nova"
test_for_return_vals 1

COMMANDS="jobsub_fetchlog jobsub_history jobsub_hold jobsub_q jobsub_release jobsub_rm  jobsub_submit jobsub_submit_dag jobsub_status"
FLAGS=" --role jelly --role jelly"
test_for_return_vals 2


COMMANDS="jobsub_fetchlog jobsub_history jobsub_hold jobsub_q jobsub_release jobsub_rm "
FLAGS=" --user fred --user fred"
test_for_return_vals 2

COMMANDS="jobsub_submit jobsub_submit_dag"
FLAGS=" --json-config foo1 --json-config foo2"
test_for_return_vals 1

COMMANDS="jobsub_fetchlog jobsub_history jobsub_hold jobsub_q jobsub_release jobsub_rm  jobsub_submit jobsub_submit_dag jobsub_status"
FLAGS=" --help"
test_for_return_vals 0

COMMANDS="jobsub_fetchlog jobsub_history jobsub_hold jobsub_q jobsub_release jobsub_rm jobsub_status"
FLAGS=" --foo bar"
test_for_return_vals 2

COMMANDS="jobsub_submit jobsub_submit_dag"
FLAGS=" --foo bar"
test_for_return_vals 1
