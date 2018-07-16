#!/bin/env bash
# file: run_pythoscope_jobsub.sh
# purpose: checks out jobsub from git
# and runs pythoscope against it, creating
# unit test stubs in jobsub/test/pythoscope
#
# author: Dennis Box, dbox@fnal.gov
#

PY-VER=2.6
VIRTUALENV_VER=virtualenv-15.1.0
WORKSPACE=.

VIRTUALENV_TARBALL=${VIRTUALENV_VER}.tar.gz
VIRTUALENV_URL="https://pypi.python.org/packages/source/v/virtualenv/$VIRTUALENV_TARBALL"
VIRTUALENV_EXE=$WORKSPACE/${VIRTUALENV_VER}/virtualenv.py
VENV=$WORKSPACE/venv-$PY_VER


rm -rf jobsub
git clone ssh://p-jobsub@cdcvs.fnal.gov/cvs/projects/jobsub

rm -f  $WORKSPACE/$VIRTUALENV_TARBALL

curl -L -o $WORKSPACE/$VIRTUALENV_TARBALL $VIRTUALENV_URL
tar xzf $WORKSPACE/$VIRTUALENV_TARBALL
rm -rf venv-15.1
mkdir venv-15.1
virtualenv-15.1.0/virtualenv.py  --system-site-packages venv-15.1/
source venv-15.1/bin/activate
pip --version
pip install pylint
pip install pythoscope
pip install asteroid
pip install astroid
pip install unittest2
pip install pepi
pip install pep8
for P in coverage rrdtool pyyaml mock xmlrunner; do pip install $P ; done 
cd jobsub
rm -rf .pythoscope/
rm rm client/logSupport.py 
mv test saveit
pythoscope --init
pythoscope *
for D in server/webapp client lib/groupsettings lib/JobsubConfigParser lib/logger server/admin ; do 
    pythoscope $D/*
done
mv tests saveit/pythoscope
mv saveit test
