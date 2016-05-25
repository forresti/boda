#'net' is a directory that you choose within './nets'
net=$1
source boda_env.sh

#using default ptt_fn="%(models_dir)/%(in_model)/trainval.prototxt')"
#boda cnet_ana --in-model=$net --print-ops=1

#assuming 'net' is an absolute or relative path from `pwd`:
boda cnet_ana --in-model=$net --print-ops=1 --ptt-fn='%(in_model)/train_val.prototxt'
#python pysrc/flops.py --ai-mnk=1 --per-layer=1 --per-layer-in-info=1
python pysrc/flops.py --print-dissertation-tex-table=1 #--ex=1 

