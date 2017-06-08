export SUBMIT_HOST=`hostname`
SOURCE_ME=/tmp/jobsub_${UID}_env.sh
grep  SetEnv /etc/httpd/conf.d/jobsub_api.conf | sed s/SetEnv/export/ | sed 's/\([A-Z]\)\ /\1=/' | sed 's/=[[:space:]]\+/=/' > $SOURCE_ME
export PYTHONPATH=$HOME/jobsub/lib/groupsettings:$HOME/jobsub/lib/logger:$HOME/jobsub/lib/JobsubConfigParser:$HOME/jobsub/server/webapp:$HOME/jobsub/server/tools:.
echo PYTHONPATH=$PYTHONPATH >> $SOURCE_ME
source $SOURCE_ME

python TestJobSettings.py
python TestNovaSettings.py
python TestMinervaSettings.py
python TestCdfSettings.py

