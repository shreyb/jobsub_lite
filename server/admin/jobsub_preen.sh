#!/bin/sh
CONFIG_FILE=/opt/jobsub/server/conf/jobsub_api.conf
SOURCE_FILE=/tmp/jobsub_preen_env.sh

grep -i SetEnv ${CONFIG_FILE} | sed -e 's/[Ss][Ee][Tt][Ee][Nn][Vv]/export/' -e 's/\([A-Z]\)\ /\1=/' -e 's/=[[:space:]]\+/=/'  > ${SOURCE_FILE}
PYTHONPATH=$(grep -i python ${CONFIG_FILE} | grep -i path | sed -e's/.*=//')
echo "export PYTHONPATH=${PYTHONPATH}" >> ${SOURCE_FILE}
source ${SOURCE_FILE}

/opt/jobsub/server/admin/jobsub_preen.py $@

if [ $? -eq 0 ] ; then
    rm ${SOURCE_FILE}
fi

