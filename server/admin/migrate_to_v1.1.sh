#!/bin/sh

usage() {
echo "usage:"
echo "$0 --dryrun : show the commands that would be executed"
echo "$0 --execute : actually execute the commands"
exit 1
}

try() { 
       if [ "$SHOULDIDOIT" = "--execute" ]; then
          "$@"
       fi 
       echo "$@"; 
      }

if [ $# != "1" ]; then
  usage
fi

if [ "$1" != "--dryrun" ]; then
   if [ "$1" != "--execute" ]; then
      usage
   fi
fi

SHOULDIDOIT=$1

cd $HOME
try tar cvf security.backup.$$.tar .security

for KEYTAB in `find .security -name '*.keytab'`; do
   try mv $KEYTAB /var/lib/jobsub/creds/keytabs
done

try chmod 755 $HOME
try chmod 755 $HOME/.security
for DIR in `find .security -type d` ; do
   try chmod 755 $DIR 
done

for OLDPROXIES in `find .security -name 'x509cc_*'`; do
   try rm $OLDPROXIES
done

for GOOD in `find /var/lib/jobsub/creds/proxies -name 'x509cc_*'` ; do
    B1=`basename $GOOD`
    D1=`dirname $GOOD`
    B2=`basename $D1`
    OLDLOC=".security/$B2/$B1"
    try ln -s $GOOD $OLDLOC
done
