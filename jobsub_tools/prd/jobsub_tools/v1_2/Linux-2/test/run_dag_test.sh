
cp $JOBSUB_TOOLS_DIR/test/test_grid_env.sh $CONDOR_EXEC/jobA.sh
cp $JOBSUB_TOOLS_DIR/test/test_grid_env.sh $CONDOR_EXEC/jobB.sh
cp $JOBSUB_TOOLS_DIR/test/test_grid_env.sh $CONDOR_EXEC/jobC.sh
cp $JOBSUB_TOOLS_DIR/test/test_grid_env.sh $CONDOR_EXEC/jobD.sh
cp $JOBSUB_TOOLS_DIR/test/test_grid_env.sh $CONDOR_EXEC/jobE.sh

dagNabbit.py -i $JOBSUB_TOOLS_DIR/test/dagTest -s
