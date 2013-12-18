#!/bin/sh
# $Id$


THISPATH=${JOBSUB_TOOLS_DIR}/bin
if [ -e /opt/condor ] ; then
     . /opt/condor/condor.sh
fi
export PATH=${THISPATH}/condor_wrappers:${PATH}
export LOCAL_CONDOR=/opt/condor/bin

if [ "$GROUP" == "" ]; then
export GROUP=`id -gn`
fi
export STORAGE_GROUP=${GROUP}
export MINERVA_SUBMIT_HOST=gpsn01.fnal.gov
export SUBMIT_HOST=gpsn01.fnal.gov

case "$GROUP"  in 


    'gm2')

	export GM2_CONDOR=/grid/fermiapp/gm2/condor/
	export GROUP_CONDOR=$GM2_CONDOR
	
	export CONDOR_TMP=/gm2/data/users/condor-tmp/${LOGNAME}
	export CONDOR_EXEC=/gm2/app/users/condor-exec/${LOGNAME}
	
	;;
    'seaquest'|'e-906'|'e906')

	#export GM2_CONDOR=/grid/fermiapp/gm2/condor/
	#export GROUP_CONDOR=$GM2_CONDOR
	export GROUP='seaquest'
	export STORAGE_GROUP='seaquest'
	export CONDOR_TMP=/seaquest/data/users/condor-tmp/${LOGNAME}
	export CONDOR_EXEC=/seaquest/app/users/condor-exec/${LOGNAME}
	
	;;

    't-962' | 'argoneut')
        export GROUP="argoneut"
        export STORAGE_GROUP="t-962"
	export ARGONEUT_CONDOR=/grid/fermiapp/argoneut/condor/
	export GROUP_CONDOR=$ARGONEUT_CONDOR
	
	export CONDOR_TMP=/argoneut/app/users/condor-tmp/${LOGNAME}
	export CONDOR_EXEC=/argoneut/app/users/condor-exec/${LOGNAME}
	
	;;

    'e938' | 'minerva')
        export GROUP="minerva"
        export STORAGE_GROUP="e938"
	export MINERVA_CONDOR=/grid/fermiapp/minerva/condor/
	export GROUP_CONDOR=$MINERVA_CONDOR
	export MINERVA_SUBMIT_HOST=gpsn01.fnal.gov
	
	export CONDOR_TMP=/minerva/app/users/condor-tmp/${LOGNAME}
	export CONDOR_EXEC=/minerva/app/users/condor-exec/${LOGNAME}
	
	;;

    'lbne')
	export LBNE_CONDOR=/grid/fermiapp/lbne/condor_scripts/
	export GROUP_CONDOR=$LBNE_CONDOR
	export CONDOR_TMP=/lbne/app/users/condor-tmp/${LOGNAME}
	export CONDOR_EXEC=/lbne/app/users/condor-exec/${LOGNAME}
	;;


    'marsmu2e')
	export MARSMU2E_CONDOR=/grid/fermiapp/marsmu2e/condor_scripts/
	export GROUP_CONDOR=$MARSMU2E_CONDOR
	export CONDOR_TMP=/mu2e/data/marsmu2e/users/condor-tmp/${LOGNAME}
	export CONDOR_EXEC=/mu2e/app/marsmu2e/users/condor-exec/${LOGNAME}
	;;


    'marsgm2')
	export MARSGM2_CONDOR=/grid/fermiapp/marsgm2/condor_scripts/
	export GROUP_CONDOR=$MARSGM2_CONDOR
	export CONDOR_TMP=/gm2/data/marsgm2/users/condor-tmp/${LOGNAME}
	export CONDOR_EXEC=/gm2/app/marsgm2/users/condor-exec/${LOGNAME}
	;;

    'marslbne')
	export MARSLBNE_CONDOR=/grid/fermiapp/marslbne/condor_scripts/
	export GROUP_CONDOR=$MARSLBNE_CONDOR
	export CONDOR_TMP=/lbne/data/marslbne/users/condor-tmp/${LOGNAME}
	export CONDOR_EXEC=/lbne/app/marslbne/users/condor-exec/${LOGNAME}
	;;

    'lbnemars')
	export LBNEMARS_CONDOR=/grid/fermiapp/lbnemars/condor_scripts/
	export GROUP_CONDOR=$LBNEMARS_CONDOR
	export CONDOR_TMP=/lbne/data/lbnemars/users/condor-tmp/${LOGNAME}
	export CONDOR_EXEC=/lbne/app/lbnemars/users/condor-exec/${LOGNAME}
	;;

    'mu2e')
	export MU2E_CONDOR=/grid/fermiapp/mu2e/condor_scripts/
	export GROUP_CONDOR=$MU2E_CONDOR
	export CONDOR_TMP=/grid/fermiapp/mu2e/condor-tmp/${LOGNAME}
	export CONDOR_EXEC=/grid/fermiapp/mu2e/condor-exec/${LOGNAME}
	#wait till these directories mounted executable
	#export CONDOR_TMP=/mu2e/app/users/condor-tmp/${LOGNAME}
	#export CONDOR_EXEC=/mu2e/app/users/condor-exec/${LOGNAME}
	;;

    'uboone' | 'microboone' )
        export GROUP="uboone"
        export STORAGE_GROUP="microboone"
	export UBOONE_CONDOR=/grid/fermiapp/uboone/condor_scripts/
	export GROUP_CONDOR=$UBOONE_CONDOR
	#export CONDOR_TMP=/grid/fermiapp/uboone/condor-tmp/${LOGNAME}
	#export CONDOR_EXEC=/grid/fermiapp/uboone/condor-exec/${LOGNAME}
	export CONDOR_TMP=/uboone/app/users/condor-tmp/${LOGNAME}
	export CONDOR_EXEC=/uboone/app/users/condor-exec/${LOGNAME}
	;;
 
    'nova')
	export NOVA_CONDOR=/grid/fermiapp/nova/condor-scripts
	export GROUP_CONDOR=$NOVA_CONDOR
	export CONDOR_TMP=/nova/data/condor-tmp/${LOGNAME}
	
	export CONDOR_EXEC=/nova/app/condor-exec/${LOGNAME}


	export NOVA_ENSTORE=/grid/fermiapp/nova/enstore
	source ${NOVA_ENSTORE}/setup_aliases.sh
	export PATH="${NOVA_ENSTORE}:${PATH}"
	;;

    'e875' | 'minos')
        export GROUP="minos"
        export STORAGE_GROUP="e875"
	export MINOS_CONDOR=/afs/fnal.gov/files/code/e875/general/condor
	export GROUP_CONDOR=$MINOS_CONDOR
	export CONDOR_TMP=/minos/data/condor-tmp/${LOGNAME}
	export CONDOR_EXEC=/minos/app/condor-exec/${LOGNAME}

	export MINERVA_SUBMIT_HOST=minos25.fnal.gov
	export SUBMIT_HOST=minos25.fnal.gov
        export X509_USER_PROXY=/local/scratch25/${LOGNAME}/grid/${LOGNAME}.proxy




	export MINOS_ENSTORE=/grid/fermiapp/minos/enstore
	source ${MINOS_ENSTORE}/setup_aliases.sh
	export PATH="${MINOS_ENSTORE}:${PATH}"

	export MINOS_GRIDDB=/grid/fermiapp/minos/griddb
	export PATH="${MINOS_GRIDDB}:${PATH}"
	;;

    *)
	echo "tried to set up with gid=$GROUP. this product will probably not work"
	;;
esac

PARENT_DIR=`dirname $CONDOR_TMP`
if [ ! -e $PARENT_DIR ]
then
    mkdir -p $PARENT_DIR
    chgrp ${STORAGE_GROUP} $PARENT_DIR
    chmod g+w $PARENT_DIR
fi

if [ ! -e $CONDOR_TMP ]
then
    mkdir -p $CONDOR_TMP
    chgrp ${STORAGE_GROUP} $CONDOR_TMP 
    chmod g+w $CONDOR_TMP
fi
	
PARENT_DIR=`dirname $CONDOR_EXEC`
if [ ! -e $PARENT_DIR ]
then
    mkdir -p $PARENT_DIR
    chgrp ${STORAGE_GROUP} $PARENT_DIR
    chmod g+w $PARENT_DIR
fi
if [ ! -e $CONDOR_EXEC ]
then
    mkdir -p $CONDOR_EXEC
    chgrp ${STORAGE_GROUP} $CONDOR_EXEC
    chmod g+w $CONDOR_EXEC
fi
    
