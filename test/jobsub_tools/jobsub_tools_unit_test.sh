export SUBMIT_HOST=`hostname`
grep  SetEnv /etc/httpd/conf.d/jobsub_api.conf | sed s/SetEnv/export/ | sed 's/\([A-Z]\)\ /\1=/' > /tmp/jobsub_${UID}_env.sh
source /tmp/jobsub_${UID}_env.sh
source $JOBSUB_UPS_LOCATION
setup jobsub_tools
export CONDOR_TMP=/tmp/condor_${UID}
export CONDOR_EXEC=/tmp/condor_${UID}
mkdir -p $CONDOR_TMP
$JOBSUB_TOOLS_DIR/test/Run_Unit_Tests.sh
STAT=$?
#I learned that my unit tests don't pass thier exit status correctly
echo "unit tests exit with status $STAT"
exit $STAT
