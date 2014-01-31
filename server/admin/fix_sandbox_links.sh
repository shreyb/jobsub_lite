#!/bin/sh
export PYTHONPATH=/opt/jobsub/lib/logger/:/opt/jobsub/lib/JobsubConfigParser/:/opt/jobsub/server/webapp
/opt/jobsub/server/admin/fix_sandbox_links.py $@
