#!/bin/csh
# $Id$


setenv THISPATH ${JOBSUB_TOOLS_DIR}/bin
if  ( -d /opt/condor ) then
     source /opt/condor/condor.csh
endif

setenv PATH ${THISPATH}/condor_wrappers:${PATH}
setenv LOCAL_CONDOR /opt/condor/bin

if ( "$GROUP" == "" ) then
   setenv GROUP "`id -gn`"
endif
setenv STORAGE_GROUP ${GROUP}

if (  "$GROUP" == "gm2"  ) then

	setenv GM2_CONDOR /grid/fermiapp/gm2/condor/
	setenv GROUP_CONDOR $GM2_CONDOR
	
	setenv CONDOR_TMP /gm2/app/users/condor-tmp/${LOGNAME}
	setenv CONDOR_EXEC /gm2/app/users/condor-exec/${LOGNAME}

else if ( ( "$GROUP" == "e-906" ) || ( "$GROUP" == "seaquest" ) ) then

        setenv GROUP "seaquest"
        setenv STORAGE_GROUP "seaquest"

	
	setenv CONDOR_TMP /seaquest/data/users/condor-tmp/${LOGNAME}
	setenv CONDOR_EXEC /seaquest/app/users/condor-exec/${LOGNAME}
	

else if ( ( "$GROUP" == "t-962" ) || ( "$GROUP" == "argoneut" ) ) then

        setenv GROUP "argoneut"
        setenv STORAGE_GROUP "t-962"

	setenv ARGONEUT_CONDOR /grid/fermiapp/argoneut/condor/
	setenv GROUP_CONDOR $ARGONEUT_CONDOR
	
	setenv CONDOR_TMP /argoneut/app/users/condor-tmp/${LOGNAME}
	setenv CONDOR_EXEC /argoneut/app/users/condor-exec/${LOGNAME}
	
	
else if ( ( "$GROUP" ==  "e938" ) || ( "$GROUP" ==  "minerva" )) then

        setenv GROUP "minerva"
        setenv STORAGE_GROUP "e938"

	setenv MINERVA_CONDOR /grid/fermiapp/minerva/condor/
	setenv GROUP_CONDOR $MINERVA_CONDOR
	
	setenv CONDOR_TMP /minerva/app/users/condor-tmp/${LOGNAME}
	setenv CONDOR_EXEC /minerva/app/users/condor-exec/${LOGNAME}
	
	

else if ( "$GROUP" ==  "lbne" ) then
	setenv LBNE_CONDOR /grid/fermiapp/lbne/condor_scripts/
	setenv GROUP_CONDOR $LBNE_CONDOR
	#setenv CONDOR_TMP /grid/fermiapp/lbne/condor-tmp/${LOGNAME}
	#setenv CONDOR_EXE /grid/fermiapp/lbne/condor-exec/${LOGNAME}
	setenv CONDOR_TMP /lbne/app/users/condor-tmp/${LOGNAME}
	setenv CONDOR_EXEC /lbne/app/users/condor-exec/${LOGNAME}


    #'marsmu2e')
else if ( "$GROUP" ==  "marsmu2e" ) then
	setenv MARSMU2E_CONDOR /grid/fermiapp/marsmu2e/condor_scripts/
	setenv GROUP_CONDOR $MARSMU2E_CONDOR
	setenv CONDOR_TMP /mu2e/data/marsmu2e/users/condor-tmp/${LOGNAME}
	setenv CONDOR_EXEC /mu2e/app/marsmu2e/users/condor-exec/${LOGNAME}
	#;;


    #'marsgm2')
else if ( "$GROUP" ==  "marsgm2" ) then

	setenv MARSGM2_CONDOR /grid/fermiapp/marsgm2/condor_scripts/
	setenv GROUP_CONDOR $MARSGM2_CONDOR
	setenv CONDOR_TMP /gm2/data/marsgm2/users/condor-tmp/${LOGNAME}
	setenv CONDOR_EXEC /gm2/app/marsgm2/users/condor-exec/${LOGNAME}
	#;;

    #'marslbne')
else if ( "$GROUP" ==  "marslbne" ) then
	setenv MARSLBNE_CONDOR /grid/fermiapp/marslbne/condor_scripts/
	setenv GROUP_CONDOR $MARSLBNE_CONDOR
	setenv CONDOR_TMP /lbne/data/marslbne/users/condor-tmp/${LOGNAME}
	setenv CONDOR_EXEC /lbne/app/marslbne/users/condor-exec/${LOGNAME}
	#;;

else if ( "$GROUP" ==  "lbnemars" ) then
    
	setenv LBNEMARS_CONDOR /grid/fermiapp/lbnemars/condor_scripts/
	setenv GROUP_CONDOR $LBNEMARS_CONDOR
	setenv CONDOR_TMP /lbne/data/lbnemars/users/condor-tmp/${LOGNAME}
	setenv CONDOR_EXEC /lbne/app/lbnemars/users/condor-exec/${LOGNAME}

	

else if ( "$GROUP" ==  "mu2e" ) then
	setenv MU2E_CONDOR /grid/fermiapp/mu2e/condor_scripts/
	setenv GROUP_CONDOR $MU2E_CONDOR
	setenv CONDOR_TMP /grid/fermiapp/mu2e/condor-tmp/${LOGNAME}
	setenv CONDOR_EXEC /grid/fermiapp/mu2e/condor-exec/${LOGNAME}
	#wait till these directories mounted executable
	#setenv CONDOR_TMP=/mu2e/app/users/condor-tmp/${LOGNAME}
	#setenv CONDOR_EXEC=/mu2e/app/users/condor-exec/${LOGNAME}
	

else if ( ("$GROUP" ==  "uboone" ) ||  ("$GROUP" == "microboone") ) then
        setenv GROUP "uboone"
        setenv STORAGE_GROUP "microboone"

	setenv UBOONE_CONDOR /grid/fermiapp/uboone/condor_scripts/
	setenv GROUP_CONDOR $UBOONE_CONDOR
	#setenv CONDOR_TMP /grid/fermiapp/uboone/condor-tmp/${LOGNAME}
	#setenv CONDOR_EXEC /grid/fermiapp/uboone/condor-exec/${LOGNAME}
	setenv CONDOR_TMP /uboone/app/users/condor-tmp/${LOGNAME}
	setenv CONDOR_EXEC /uboone/app/users/condor-exec/${LOGNAME}
	
 
else if ( "$GROUP" ==  "nova" ) then
	setenv NOVA_CONDOR /grid/fermiapp/nova/condor-scripts
	setenv GROUP_CONDOR $NOVA_CONDOR
	setenv CONDOR_TMP /nova/data/condor-tmp/${LOGNAME}
	
	setenv CONDOR_EXEC /nova/app/condor-exec/${LOGNAME}


	setenv NOVA_ENSTORE /grid/fermiapp/nova/enstore
	source ${NOVA_ENSTORE}/setup_aliases.csh
	setenv PATH "${NOVA_ENSTORE}:${PATH}"
	

else if ( ("$GROUP" ==  "e875" ) ||  ("$GROUP" == "minos") ) then
        setenv GROUP "minos"
        setenv STORAGE_GROUP "e875"
  
	setenv MINOS_CONDOR /afs/fnal.gov/files/code/e875/general/condor
	setenv GROUP_CONDOR $MINOS_CONDOR
	setenv CONDOR_TMP /minos/data/condor-tmp/${LOGNAME}
	setenv CONDOR_EXEC /minos/app/condor-exec/${LOGNAME}



	setenv MINOS_ENSTORE /grid/fermiapp/minos/enstore
	source ${MINOS_ENSTORE}/setup_aliases.csh
	setenv PATH "${MINOS_ENSTORE}:${PATH}"

	setenv MINOS_GRIDDB /grid/fermiapp/minos/griddb
	setenv PATH "${MINOS_GRIDDB}:${PATH}"
	

else
	echo "don't know what to do with GROUP=$GROUP. jobsub script may not work"
	
endif

setenv PARENT_DIR `dirname $CONDOR_TMP`

if ( ! -d $PARENT_DIR ) then

    mkdir -p $PARENT_DIR
    chgrp ${STORAGE_GROUP} $PARENT_DIR 
    chmod g+w $PARENT_DIR
endif

if ( ! -d $CONDOR_TMP ) then

    mkdir -p $CONDOR_TMP
    chgrp ${STORAGE_GROUP} $CONDOR_TMP 
    chmod g+w $CONDOR_TMP
endif
	
setenv PARENT_DIR `dirname $CONDOR_EXEC`

if ( ! -d $PARENT_DIR ) then

    mkdir -p $PARENT_DIR
    chgrp ${STORAGE_GROUP} $PARENT_DIR
    chmod g+w $PARENT_DIR
   
endif


if ( ! -d $CONDOR_EXEC ) then

    mkdir -p $CONDOR_EXEC
    chgrp ${STORAGE_GROUP} $CONDOR_EXEC
    chmod g+w $CONDOR_EXEC
   
endif
