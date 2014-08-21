#!/bin/sh -x
cd $JOBSUB_TOOLS_DIR/pylib/groupsettings
/usr/bin/env python ./TestJobSettings.py
/usr/bin/env python ./TestMinervaSettings.py
/usr/bin/env python ./TestNovaSettings.py
/usr/bin/env python ./TestLbneSettings.py
/usr/bin/env python ./TestCdfSettings.py
cd -
cd $JOBSUB_TOOLS_DIR/test
./jobsub_ups_unit_test.sh 
cd -
