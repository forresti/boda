# pretty printing stuff. factor out somewhere?
def pad( v, s ): return s + " "*max(0,v - len(s))
def pp_val_part( v, force ):
    if v < 10: return "%.2f" % v
    if v < 100: return "%.1f" % v
    if (v < 1000) or force: return "%.0f" % v
    return None
def pp_val( v ): # pretty-print flops
    exp = 0
    assert v >= 0
    if v == 0: return "0"
    while v < 1.0:
        v *= 1000.0
        exp -= 1
    ret = pp_val_part( v, 0 )
    while ret is None:
        v /= 1000.0
        exp += 1
        ret = pp_val_part( v, exp == 5 )
    if exp < -4: return str(v) # too small, give up
    #print "v",v,"exp",exp
    if exp < 0: return ret+"munp"[- 1 - exp]
    if exp == 0: return ret
    return ret+"KMGTP"[exp - 1]

def pp_pc( v ): return "%.1f%%" % (v*100.0,)
verbose_print = 0
if verbose_print:
    def pp_secs( v ): return pp_val( v ) + " SECS"
    def pp_flops( v ): return pp_val( v ) + " FLOPS"
    def pp_bytes( v ): return pp_val( v ) + " BYTES"
    def pp_bps( v ): return pp_val( v ) + " BYTES/SEC"
    def pp_fpb( v ): return pp_val( v ) + " FLOPS/BYTE"
    def pp_fps( v ): return pp_val( v ) + " FLOPS/SEC"
    def pp_fpspw( v ): return pp_val( v ) + " FLOPS/SEC/WATT"
    def pp_joules( v ): return pp_val( v ) + " JOULES"
else:
    def pp_secs( v ): return pp_val( v ) + "s"
    def pp_flops( v ): return pp_val( v ) + "F"
    def pp_bytes( v ): return pp_val( v ) + "B"
    def pp_bps( v ): return pp_val( v ) + "B/s"
    def pp_fpb( v ): return pp_val( v ) + "F/B"
    def pp_fps( v ): return pp_val( v ) + "F/s"
    def pp_fpspw( v ): return pp_val( v ) + "F/s/W"
    def pp_joules( v ): return pp_val( v ) + "J"


import operator

# cnet flop-calculating ops classes
class NDA( object ): 
    def __init__( self, name, *args ):
        self.name = name
        self.dims = args
        if len(args) == 4:
            self.num = args[0]
            self.chan = args[1]
            self.y = args[2]
            self.x = args[3]

    def dims_str( self ): return "*".join( str(d) for d in self.dims )
    def dims_prod( self ): 
        if hasattr(self,"dims"): return reduce(operator.mul, self.dims, 1)
        return self.num*self.chan*self.y*self.x
    def dims_info_str( self ): return self.dims_str()+"="+pp_bytes(self.dims_prod()*4)
    def __getitem__( self, *args, **kwargs ):
        return self
    def __mul__( self, o ):
        #if hasattr(self,"dims"): print len(self.dims)
        #else: print "4"
        return self

class Net( object ):
    def __init__( self, args ):
        self.args = args
        self.tot_forward_flops = 0
        self.tot_forward_bytes = 0
        self.tot_backward_flops = 0
        self.tot_backward_bytes = 0
        self.tot_filt_bytes = 0;
        self.tot_in_bytes = 0;
        self.ndas = {}
        self.ops = []
    def add_nda( self, vn, nda ): self.ndas[vn] = nda
    def add_op( self, op ): self.ops.append( op )

    def print_stats( self ):


        if net.args.print_dissertation_tex_table:
            print "total & & & & & & & ", 
            print pp_bytes(self.tot_in_bytes), "&", pp_bytes(self.tot_filt_bytes), "&", pp_flops(self.tot_forward_flops),
            print "\\\ \hline"

        print "-- INPUT: RUNTIME=%ss --"% (args.runtime, )
        print "-- INPUT: POWER=%sW --" % (args.power, )
        if "data" in self.ndas: print "-- \"data\" node dims: ", self.ndas["data"].dims_info_str()

        fb_str = "FWD"
        if verbose_print: fb_str = "FORWARD"
        print "--- %s TOTALS ---" % fb_str
        flops = self.tot_forward_flops
        bytes_ = self.tot_forward_bytes

        if self.tot_backward_flops:
            fb_str = "FORWARD+BACKWARD"
            flops += self.tot_backward_flops
            bytes_ += self.tot_backward_bytes

        print pp_flops(flops), pp_fps(flops/args.runtime)
        print pp_bytes(bytes_), pp_bps(bytes_/args.runtime), "AI="+pp_fpb(flops / float(bytes_)) #includes filters & input & output activations per layer
        print"TOTAL ACTIVATIONS="+pp_bytes(self.tot_in_bytes) #total activations of all layers. (tot_in_bytes = total input activations over all layers)
        print pp_joules(args.power*args.runtime), pp_fpspw(flops/args.runtime/args.power) 
        if self.args.print_tex_table_entry:
            print( "%-20s & %-20s & %-20s & %-20s & %-20s\\hline" % 
                   (self.args.net_name,pp_bytes(self.tot_in_bytes),pp_bytes(self.tot_filt_bytes),
                    pp_val_part(float(self.tot_in_bytes)/float(self.tot_filt_bytes), 1), 
                    pp_flops(flops)  ) )


#format: layerName & filter HxW & stride & chansOut & output HxW & outputMB & filtersMB & flops
def dissertation_table_row(name, filt_y, filt_x, stride, chansOut, output_y, output_x, outputMB, filtersMB, flops):

        print name.replace('_',''), '&', #converts 'conv_1' --> 'conv1'
        print '%dx%d'%(filt_y, filt_x), '&', stride, '&', chansOut, '&',
        print '%dx%d'%(output_y, output_x), '&', 
        print outputMB, '&', filtersMB, '&', flops,
        print "\\\ \hline"



class Convolution( object ): 
    def __init__( self, name, bot_names, top_names, in_pad, stride, kern_sz, out_chans=0, conv_has_relu=0 ): 
        # note: ignores in_pad and stride, but they sort-of aren't
        # needed since the output size is calculated using them. we
        # could use them as a check here, but that would require
        # duplicating the in-out calculation code?
        global net
        assert len(bot_names) == 3
        assert len(top_names) == 1
        bot = net.ndas[bot_names[0]]
        top = net.ndas[top_names[0]]
        filts = net.ndas[bot_names[1]]
        biases = net.ndas[bot_names[2]]

        in_pels = bot.dims_prod()
        out_pels = top.dims_prod()

        K = filts.chan*filts.x*filts.y
        N = filts.num
        M = top.x*top.y*top.num # note: all-imgs M

        if net.args.per_layer_in_info:
            print name, "input", bot.dims_info_str(), "filts", filts.dims_info_str(), "out", top.dims_info_str()

        net.tot_filt_bytes += filts.dims_prod() * 4
        net.tot_in_bytes += in_pels * 4

        forward_bytes = (in_pels + out_pels + filts.dims_prod() + biases.dims_prod()) * 4

        net.tot_forward_bytes += forward_bytes
            
        assert bot.chan == filts.chan # filt.chan is (or should be) input chans
        assert top.chan == filts.num # filt.num is (or should be) output chans
        # note: top.{x,y} should be = ( bot.{x,y} + pad ) / stride   (ceild/floord correctly)
        forward_flops = out_pels * filts.x * filts.y * filts.chan * 2
        grad_inner_dim = out_pels / filts.num # aka number of input patches
        assert grad_inner_dim == top.num*top.x*top.y

        net.tot_forward_flops += forward_flops

        stride_int = [int(s) for s in stride.split(' ')]
        #print stride_int

        #format: layerName & filter HxW & stride & chansOut & output HxW & outputMB & filtersMB & flops
        if net.args.print_dissertation_tex_table:
            outputMB = pp_bytes(in_pels*4)
            filtersMB = pp_bytes( (filts.dims_prod() + biases.dims_prod())*4 )
            flops = pp_flops(forward_flops)

            #print row of table:
            dissertation_table_row(name, filts.y, filts.x, stride_int[0], filts.num, top.y, top.x, outputMB, filtersMB, flops) 

        #TODO: line in table for sum over all layers: inputMB, filtersMB, flops

        if net.args.per_layer:
            print name,
            print "FWD",pp_flops(forward_flops),pp_bytes(forward_bytes),
            if net.args.ai_mnk:
                print " FWD_AI", pp_fpb( forward_flops / float(forward_bytes) ),
                print " MxNxK=%sx%sx%s" % (M,N,K),
            plt = per_layer_time.get(name,None)
            if plt:
                print " --- ", pp_secs( plt ), pp_fps( forward_flops / float(plt) ),
            print ""

class BckConv( object ): 
    def __init__( self, name, bot_names, top_names, in_pad, stride, kern_sz ): 
        global net
        assert len(bot_names) == 4
        assert len(top_names) == 3

        bot = net.ndas[bot_names[0]]
        filts = net.ndas[bot_names[1]]
        biases = net.ndas[bot_names[2]]
        top = net.ndas[bot_names[3]] # aka out_grad_loss


        bot_grad_loss = net.ndas[top_names[0]]
        filts_grad_loss = net.ndas[top_names[1]]
        biases_grad_loss = net.ndas[top_names[2]]

        in_pels = bot.dims_prod()
        out_pels = top.dims_prod()

        K = filts.chan*filts.x*filts.y
        N = filts.num
        M = top.x*top.y*top.num # note: all-imgs M

        backward_bytes = (in_pels*2 + out_pels + filts.dims_prod()*2 + biases.dims_prod()*2) * 4

        net.tot_backward_bytes += backward_bytes
            
        grad_inner_dim = out_pels / filts.num # aka number of input patches
        assert grad_inner_dim == top.num*top.x*top.y
        back_grad_flops = filts.dims_prod() * grad_inner_dim * 2 # grad is same size as filts
        diff_inner_dim = filts.num
        # diff ends up as the same size as input but is reduced from a temp of size im2col(input).
        back_diff_flops = (filts.chan*filts.x*filts.y)*diff_inner_dim*grad_inner_dim * 2  # as: (M) * N * K

        back_flops = back_diff_flops + back_grad_flops
        net.tot_backward_flops += back_flops

        if net.args.per_layer:
            print name,
            print "BCK",pp_flops(back_flops),pp_bytes(backward_bytes),
            if net.args.ai_mnk:
                print " BCK_AI", pp_fpb( back_flops / float(backward_bytes) ),
                print " fg-MxNxK=%sx%sx%s" % (K,N,M),
                print " ig-MxNxK=%sx%sx%s" % (M,K,N),
            plt = per_layer_time.get(name,None)
            if plt:
                print " --- ", pp_secs( plt ), pp_fps( back_flops / float(plt) ),
            print ""


# FIXME: in boda output, the ops/nodes of IP layers are printed out as if it
# they were conv layers ... not ideal, since NDAs don't match caffe iface
# for innerproduct. hmm.
InnerProduct=Convolution 

# stubs to ignore for now
class Pooling( object ): 
    #def __init__( self, **kwargs ): self.opts = kwargs
    def __init__( self, name, bot_names, top_names, in_pad, stride, kern_sz, out_chans=0, avg_pool=0):
        bot = net.ndas[bot_names[0]]
        #top = net.ndas[bot_names[1]]

        #TODO: handle globalpool?

        stride_int = [int(s) for s in stride.split(' ')]

        new_x = bot.x/stride_int[0] #TODO: round
        print new_x

        print name
        print 'bot:', bot.x, bot.y, bot.num, bot.chan
        #print 'top.size:', top.size
        print 'in_pad:',in_pad
        print 'stride:',stride

        #TODO: estimate of computation

class LRN( object ): 
    def __init__( self, **kwargs ): self.opts = kwargs
class Concat( object ): 
    def __init__( self, **kwargs ): self.opts = kwargs
class ReLU( object ): 
    def __init__( self, **kwargs ): self.opts = kwargs
class Dropout( object ): 
    def __init__( self, **kwargs ): self.opts = kwargs
class Softmax( object ): 
    def __init__( self, **kwargs ): self.opts = kwargs
class SoftmaxWithLoss( object ): 
    def __init__( self, **kwargs ): self.opts = kwargs
class Spreading( object ): 
    def __init__( self, **kwargs ): self.opts = kwargs
class ZeroIfNonPos( object ): 
    def __init__( self, **kwargs ): self.opts = kwargs
class Split( object ): 
    def __init__( self, **kwargs ): self.opts = kwargs
class Reduce( object ): 
    def __init__( self, **kwargs ): self.opts = kwargs
class BckLRN( object ): 
    def __init__( self, **kwargs ): self.opts = kwargs

import argparse
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--net-fn', metavar="FN", type=str, default="out.py", help="filename of network-definition python script" )
parser.add_argument('--net-name', metavar="STR", type=str, default="ANON_NET", help="name of network (for printouts)" )
parser.add_argument('--runtime', metavar='SECONDS', type=float, default=1, help='time taken for power/energy calculations')
parser.add_argument('--power', metavar='WATTS', type=float, default=200, help='average power used over runtime')
parser.add_argument('--ai-mnk', metavar='BOOL', type=int, default=0, help='1:show fwd AI and MxNxK; 0:do not show')
parser.add_argument('--per-layer', metavar='BOOL', type=int, default=0, help='1:print per-layer info; 0:only summary')
parser.add_argument('--per-layer-in-info', metavar='BOOL', type=int, default=0, help='if non-zero print per-layer input dims info')
parser.add_argument('--profile', metavar='BOOL', type=int, default=0, help='if non-zero print per-layer sorted profile')
parser.add_argument('--print-tex-table-entry', metavar='BOOL', type=int, default=0, help='if non-zero print one-off tex table entry')
parser.add_argument('--print-dissertation-tex-table', metavar='BOOL', type=int, default=0, help='if non-zero print one-off tex table entry')

args = parser.parse_args()
net = Net(args)
per_layer_time = {}

if net.args.print_dissertation_tex_table:
    print 'layer & filter HxW & stride & channelsOut & output HxW & Qty of output (MB) & Qty of filters (MB) & Computation (FLOPS) \\\ \hline'


# source cnet decl
execfile( args.net_fn )

net.print_stats()

if 1:
    tot_inxp = 0
    for k,v in per_layer_time.iteritems():
        if k.endswith("_inxp"): tot_inxp += v
    print "total _inxp time: ", pp_secs(tot_inxp)

if net.args.profile:
    lts = [ (t,ln) for ln,t in per_layer_time.iteritems() ]
    lts.sort()
    t = 0.0
    print "PROFILE:"
    print "".join( pad(10,v) for v in ["time","time%","cum_time","cum_time%","func_name"] )
    for k,v in reversed(lts):
        kf = float(k)
        t += kf
        print "".join( pad(10,v) for v in [pp_secs(kf),pp_pc(kf/net.args.runtime),pp_secs(t),pp_pc(t/net.args.runtime), v] )

