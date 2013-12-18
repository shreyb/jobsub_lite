#!/bin/sh
# $Id$


#THISPATH=/grid/fermiapp/common/tools
THISPATH=`pwd`
if [ -e /opt/condor ] ; then
     . /opt/condor/condor.sh
fi
export PATH=${PATH}:/grid/fermiapp/common/tools/condor_wrappers
export LOCAL_CONDOR=/opt/condor/bin

if [ "$GROUP" == "" ]; then
export GROUP=`id -gn`
fi
export STORAGE_GROUP=${GROUP}

case "$GROUP"  in 


    'gm2')

	export GM2_CONDOR=/grid/fermiapp/gm2/condor/
	export GROUP_CONDOR=$ARGONEUT_CONDOR
	
	export CONDOR_TMP=/gm2/app/users/condor-tmp/${LOGNAME}
	export CONDOR_EXEC=/gm2/app/users/condor-exec/${LOGNAME}
	
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
	
	export CONDOR_TMP=/minerva/app/users/condor-tmp/${LOGNAME}
	export CONDOR_EXEC=/minerva/app/users/condor-exec/${LOGNAME}
	
	;;

    'lbne')
	export LBNE_CONDOR=/grid/fermiapp/lbne/condor_scripts/
	export GROUP_CONDOR=$LBNE_CONDOR
	export CONDOR_TMP=/lbne/app/users/condor-tmp/${LOGNAME}
	export CONDOR_EXEC=/lbne/app/users/condor-exec/${LOGNAME}
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

    'coupp' | 'e961')
	export CONDOR_TMP=/coupp/data/condor-tmp/${LOGNAME}
	export CONDOR_EXEC=/coupp/app/condor-exec/${LOGNAME}
	;;

    'e875' | 'minos')
        export GROUP="minos"
        export STORAGE_GROUP="e875"
	export MINOS_CONDOR=/afs/fnal.gov/files/code/e875/general/condor
	export GROUP_CONDOR=$MINOS_CONDOR
	export CONDOR_TMP=/minos/data/condor-tmp/${LOGNAME}
	export CONDOR_EXEC=/minos/app/condor-exec/${LOGNAME}

	export PATH="${MINOS_CONDOR}/scripts:${PATH}"


	export MINOS_ENSTORE=/grid/fermiapp/minos/enstore
	source ${MINOS_ENSTORE}/setup_aliases.sh
	export PATH="${MINOS_ENSTORE}:${PATH}"

	export MINOS_GRIDDB=/grid/fermiapp/minos/griddb
	export PATH="${MINOS_GRIDDB}:${PATH}"
	;;

    *)
	echo "don't know what to do with GROUP=$GROUP. jobsub script may not work"
	;;
esac


if [ ! -e $CONDOR_TMP ]
then
    mkdir -p $CONDOR_TMP
    chgrp ${STORAGE_GROUP} $CONDOR_TMP 
    chmod g+w $CONDOR_TMP
fi
	
if [ ! -e $CONDOR_EXEC ]
then
    mkdir -p $CONDOR_EXEC
    chgrp ${STORAGE_GROUP} $CONDOR_EXEC
    chmod g+w $CONDOR_EXEC
fi
    
export PATH="${LOCAL_CONDOR}:${PATH}"
#
#remember to do something with condor_wrappers here 
#
export PATH="${GROUP_CONDOR}:${PATH}"
export PATH="${GROUP_CONDOR}/condor_wrappers:${PATH}"
export PATH="${THISPATH}:${PATH}"
export PYTHONPATH="${THISPATH}/groupsettings:${PYTHONPATH}"
