#!/bin/bash
# run as ./jobsub/packaging/package.sh from directory above jobsub
VERS=jobsub-0.1.1
REL=2
echo "%_topdir ${HOME}/rpm" > ~/.rpmmacros
echo "%_tmppath /tmp" >> ~/.rpmmacros
mkdir -p ~/rpm/BUILD ~/rpm/RPMS ~/rpm/SOURCES ~/rpm/SPECS ~/rpm/SRPMS
cp ./jobsub/packaging/jobsub_server.spec ~/rpm/SPECS
mv ./jobsub ./${VERS}
tar --exclude="*.pyc" --exclude="*client*" --exclude=".*" --exclude="doc" --exclude="packaging" --exclude="*.log" --exclude="*.sock" --exclude="dev_use_virtual_env.sh" --exclude="Readme" --exclude="setup" --exclude="*.pyo" --exclude="requirements.txt" -cf ${VERS}.tar -v ${VERS}
mv ./${VERS} ./jobsub
gzip ${VERS}.tar
mv ${VERS}.tar.gz ~/rpm/SOURCES/
rpmbuild -bb ~/rpm/SPECS/jobsub_server.spec
cp ~/rpm/RPMS/noarch/${VERS}-${REL}.noarch.rpm ./jobsub/packaging
# TODO: the RPM has to be put someplace that the server admin can download it. Probably the yum repo.
