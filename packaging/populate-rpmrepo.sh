#!/bin/sh

usage="USAGE: $0 <path to rpm file> [prod]"
remote_cmd() {
    cmd=$1
    ssh $repologin "$cmd"
}

rpmfile=$1
repo=$2

if [ "$rpmfile" = "" ]; then
    echo "Specify rpm file"
    echo $usage
    exit 1
fi

repologin="jobsub@web1.fnal.gov"
repodir='/var/www/html/files/jobsub'
#For now only SL6 support
versionlist='6'
#For now only 64bit support
archlist='x86_64'
# Create repo for dev (developers) and one for production (operations)
flavors='dev'

#make changes where appropiate (eg: scp new rpms)
for flavor in $flavors; do
    for version in $versionlist; do
        for arch in $archlist; do
            workdir="$repodir/$flavor/$version/$arch"
            remote_cmd "mkdir -p $workdir"
            scp $rpmfile "$repologin:$workdir"
            remote_cmd "createrepo $workdir"
            #remote_cmd "chmod -R g+w $workdir"
         done
    done
done
