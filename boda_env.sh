#export BODA_HOME=~/git_work/boda
export BODA_HOME=~/boda
#export LD_LIBRARY_PATH=~/git_work/caffe_dev/build/lib
export LD_LIBRARY_PATH=/nscratch/forresti/caffe-bvlc-master/build/lib:$LD_LIBRARY_PATH
#export LD_LIBRARY_PATH=/nscratch/forresti/caffe-bvlc-master/caffe-repro-cuDNN-NiN-bug/build/lib:$LD_LIBRARY_PATH
export PATH=${BODA_HOME}/lib:$PATH
. ${BODA_HOME}/boda_completion.bash

