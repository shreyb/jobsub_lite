#!/bin/sh
# $Id$

if [ ! -e "$VDT_LOCATION" ] ; then
for FILE in /home/grid/vdt2.0/setup.sh /home/lbne/software/setup.sh /usr/local/vdt/setup.sh /grid/app/minos/VDT/setup.sh ; do
        if [ -e  "$FILE" ] ; then
                ##echo "found $FILE, setting up VDT "
		. $FILE
                break
        fi
done
fi

echo $PYTHONPATH | grep pexpect

if [ $? ]; then
. /grid/fermiapp/common/pexpect/setpath.sh
fi

if [ -e "./request_robot_cert.sh" ]; then
     ./request_robot_cert.py $*
else
     /grid/fermiapp/common/tools/request_robot_cert.py $*
fi
