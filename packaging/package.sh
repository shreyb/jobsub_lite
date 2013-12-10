#!/bin/bash
# run as ./jobsub/packaging/package.sh from directory above jobsub
echo "%_topdir ${HOME}/rpm" > ~/.rpmmacros
echo "%_tmppath /tmp" >> ~/.rpmmacros
mkdir -p ~/rpm/BUILD ~/rpm/RPMS ~/rpm/SOURCES ~/rpm/SPECS ~/rpm/SRPMS
cp ./jobsub/packaging/jobsub_server.spec ~/rpm/SPECS
mv ./jobsub ./jobsub-1.0
tar --exclude="*.pyc" --exclude="*client*" --exclude=".*" --exclude="doc" --exclude="packaging" --exclude="*.log" --exclude="*.sock" --exclude="dev_use_virtual_env.sh" --exclude="Readme" --exclude="setup" --exclude="*.pyo" --exclude="requirements.txt" -cf jobsub-1.0.tar -v jobsub-1.0
mv ./jobsub-1.0 ./jobsub
gzip jobsub-1.0.tar
mv jobsub-1.0.tar.gz ~/rpm/SOURCES/
rpmbuild -bb ~/rpm/SPECS/jobsub_server.spec
cp ~/rpm/RPMS/noarch/jobsub-1.0-0.noarch.rpm ./jobsub/packaging
