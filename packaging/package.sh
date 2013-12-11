#!/bin/bash
# run as ./jobsub/packaging/package.sh from directory above jobsub
echo "%_topdir ${HOME}/rpm" > ~/.rpmmacros
echo "%_tmppath /tmp" >> ~/.rpmmacros
mkdir -p ~/rpm/BUILD ~/rpm/RPMS ~/rpm/SOURCES ~/rpm/SPECS ~/rpm/SRPMS
cp ./jobsub/packaging/jobsub_server.spec ~/rpm/SPECS
mv ./jobsub ./jobsub-0.1
tar --exclude="*.pyc" --exclude="*client*" --exclude=".*" --exclude="doc" --exclude="packaging" --exclude="*.log" --exclude="*.sock" --exclude="dev_use_virtual_env.sh" --exclude="Readme" --exclude="setup" --exclude="*.pyo" --exclude="requirements.txt" -cf jobsub-0.1.tar -v jobsub-0.1
mv ./jobsub-0.1 ./jobsub
gzip jobsub-0.1.tar
mv jobsub-0.1.tar.gz ~/rpm/SOURCES/
rpmbuild -bb ~/rpm/SPECS/jobsub_server.spec
cp ~/rpm/RPMS/noarch/jobsub-0.1-0.noarch.rpm ./jobsub/packaging
# TODO: the RPM has to be put someplace that the server admin can download it. Probably the yum repo.
