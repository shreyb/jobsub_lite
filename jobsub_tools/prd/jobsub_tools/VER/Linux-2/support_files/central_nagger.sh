#!/bin/sh -x
SCRIPT=/home/grid/scripts/nag_old_condor_files.py
OUTDIR=/home/grid/script.output

#argoneut
$SCRIPT /argoneut/data/users/condor-tmp > $OUTDIR/argoneut.data.users.condor-tmp
$SCRIPT /argoneut/app/users/condor-exec > $OUTDIR/argoneut.app.users.condor-exec

#coupp
$SCRIPT /coupp/data/condor-tmp > $OUTDIR/coupp.data.condor-tmp
$SCRIPT /coupp/app/condor-exec > $OUTDIR/coupp.app.condor-exec

#d0
$SCRIPT /d0/data/condor-tmp > $OUTDIR/d0.data.condor-tmp
$SCRIPT /d0/app/condor-exec > $OUTDIR/d0.app.condor-exec


#gm2
$SCRIPT /gm2/data/users/condor-tmp > $OUTDIR/gm2.data.users.condor-tmp
$SCRIPT /gm2/app/users/condor-exec > $OUTDIR/gm2.app.users.condor-exec

#lbne
$SCRIPT /grid/fermiapp/lbne/condor-tmp > $OUTDIR/grid.fermiapp.lbne.condor-tmp
$SCRIPT /grid/fermiapp/lbne/condor-exec > $OUTDIR/grid.fermiapp.lbne.condor-exec
$SCRIPT /lbne/app/users/condor-tmp  > $OUTDIR/lbne.app.users.condor-tmp
$SCRIPT /lbne/app/users/condor-exec  > $OUTDIR/lbne.app.users.condor-exec

#marsgm2
$SCRIPT /gm2/data/marsgm2/users/condor-tmp > $OUTDIR/gm2.data.marsgm2.users.condor-tmp
$SCRIPT /gm2/data/marsgm2/users/condor-exec > $OUTDIR/gm2.data.marsgm2.users.condor-exec

#marslbne
$SCRIPT /lbne/data/marslbne/users/condor-tmp > $OUTDIR/lbne.data.marslbne.users.condor-tmp
$SCRIPT /lbne/app/marslbne/users/condor-exec > $OUTDIR/lbne.data.marslbne.users.condor-exec

#marsmu2e
$SCRIPT /mu2e/data/marsmu2e/users/condor-tmp > $OUTDIR/mu2e.data.mars.mu2e.users.condor-tmp
$SCRIPT /mu2e/app/marsmu2e/users/condor-exec > $OUTDIR/mu2e.data.mars.mu2e.users.condor-exec

#minerva
$SCRIPT /grid/data/minerva/condor-tmp > $OUTDIR/grid.data.condor-tmp
$SCRIPT /grid/data/minerva/condor-exec > $OUTDIR/grid.data.condor-exec
$SCRIPT /minerva/app/users/condor-tmp  > $OUTDIR/minerva.app.users.condor-tmp
$SCRIPT /minerva/app/users/condor-exec > $OUTDIR/minerva.app.users.condor-exec

#minos
$SCRIPT /minos/data/condor-tmp > $OUTDIR/minos.data.condor-tmp
$SCRIPT /minos/app/condor-exec > $OUTDIR/minos.app.condor-exec

#mu2e
$SCRIPT /grid/fermiapp/mu2e/condor-tmp > $OUTDIR/grid.fermiapp.mu2e.condor-tmp
$SCRIPT /grid/fermiapp/mu2e/condor-exec > $OUTDIR/grid.fermiapp.mu2e.condor-exec
$SCRIPT /mu2e/app/users/condor-tmp  > $OUTDIR/mu2e.app.users.condor-tmp
$SCRIPT /mu2e/app/users/condor-exec  > $OUTDIR/mu2e.app.users.condor-exec

#nova
$SCRIPT /nova/data/condor-tmp > $OUTDIR/nova.data.condor-tmp
$SCRIPT /nova/app/condor-exec > $OUTDIR/nova.app.condor-exec

#uboone/microboone
$SCRIPT /grid/fermiapp/uboone/condor-exec > $OUTDIR/grid.fermiapp.uboone.condor-exec
$SCRIPT /grid/fermiapp/uboone/condor-tmp > $OUTDIR/grid.fermiapp.uboone.condor-tmp
$SCRIPT /uboone/app/users/condor-tmp > $OUTDIR/uboone.app.users.condor-tmp
$SCRIPT /uboone/app/users/condor-exec > $OUTDIR/uboone.app.users.condor-exec

#seaquest
$SCRIPT /e906/data/users/condor-tmp > $OUTDIR/e906.data.users.condor-tmp
$SCRIPT /e906/app/users/condor-exec > $OUTDIR/e906.app.users.condor-exec
