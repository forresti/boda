#'net' is a directory that you choose within './nets'
net=$1
source boda_env.sh
#ptt_fn="%(models_dir)/%(in_model)/trainval.prototxt')" #ovreride from 'train_val' --> 'trainva;'
boda cnet_ana --in-model=$net --print-ops=1 #--ptt-fn=$ptt_fn
#python pysrc/flops.py --ai-mnk=1 --per-layer=1 --per-layer-in-info=1
python pysrc/flops.py --print-dissertation-tex-table=1 

