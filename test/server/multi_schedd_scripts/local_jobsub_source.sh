#!/bin/sh
cd /opt/jobsub/server/webapp
/bin/rm *
ln -s ~dbox/jobsub/server/webapp/* .
cd /opt/jobsub/server/tools
/bin/rm *
ln -s ~dbox/jobsub/server/tools/* .
cd /opt/jobsub/lib/groupsettings
/bin/rm *
ln -s ~dbox/jobsub/lib/groupsettings/* .
cd /opt/jobsub/lib/DAGParser
/bin/rm *
ln -s ~dbox/jobsub/lib/DAGParser/* .
service httpd restart
