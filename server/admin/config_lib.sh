
function get_jobsub_env {
export JOBSUB_API_CONF=/opt/jobsub/server/conf/jobsub_api.conf
export JOBSUB_ADMIN_ENV=/tmp/$(whoami).jobsub_admin_env.sh
echo -n '# generated on ' > $JOBSUB_ADMIN_ENV
date >> $JOBSUB_ADMIN_ENV
grep -i 'define ' $JOBSUB_API_CONF | sed -e 's/[Dd][Ee][Ff][Ii][Nn][Ee]/export/' -e 's/ \//=\//'  >> $JOBSUB_ADMIN_ENV
grep -i 'SetEnv ' $JOBSUB_API_CONF | sed -e 's/[Ss][Ee][Tt][Ee][Nn][Vv]/export/' -e 's/\([A-Z]\)\ /\1=/' -e 's/=[[:space:]]\+/=/'  >> $JOBSUB_ADMIN_ENV
grep python-path  $JOBSUB_API_CONF | sed -e 's/.*python-path/export PYTHONPATH/' -e 's/=[[:space:]]\+//'>>$JOBSUB_ADMIN_ENV
source $JOBSUB_ADMIN_ENV
}


