// Copyright (c) 2013-2014, Matthew W. Moskewicz <moskewcz@alumni.princeton.edu>; part of Boda framework; see LICENSE
#include"boda_tu_base.H"
#include"timers.H"
#include"str_util.H"
#include"conv_util.H"
#include"lexp.H"
#include"nesi.H"
#include"caffepb.H"
#include"caffe/proto/caffe.pb.h"
//#include<google/protobuf/text_format.h> // unused, would make sense to include here

namespace boda 
{

  template< typename CP > void set_param_from_conv_op( CP & cp, p_conv_op_t conv_op ) {
    // TODO/NOTE: non-square (_w/_h) handling is untested
    // SIGH: three cases are not quite consistent enough to be worth folding/sharing things more?
    cp.clear_pad_w(); cp.clear_pad_h(); cp.clear_pad();
    assert_st( conv_op->in_pad.bnds_are_same() ); // caffe can't handle different padding on +- edges
    u32_pt_t const & pad = conv_op->in_pad.p[0];
    if( pad.dims_are_same() ) { cp.set_pad( pad.d[0] ); }
    else { cp.set_pad_w( pad.d[0] ); cp.set_pad_h( pad.d[1] ); }

    cp.clear_kernel_w(); cp.clear_kernel_h(); cp.clear_kernel_size();
    if( conv_op->kern_sz.dims_are_same() ) { cp.set_kernel_size( conv_op->kern_sz.d[0] ); }
    else { cp.set_kernel_w( conv_op->kern_sz.d[0] ); cp.set_kernel_h( conv_op->kern_sz.d[1] ); }

    cp.clear_stride_w(); cp.clear_stride_h(); cp.clear_stride();
    if( conv_op->stride.dims_are_same() ) { cp.set_stride( conv_op->stride.d[0] ); }
    else { cp.set_stride_w( conv_op->stride.d[0] ); cp.set_stride_h( conv_op->stride.d[1] ); }
  }
  template void set_param_from_conv_op< caffe::ConvolutionParameter >( caffe::ConvolutionParameter & cp, p_conv_op_t conv_op );

  template< typename CP > p_conv_op_t get_conv_op_from_param( CP const & cp ) {
    p_conv_op_t conv_op( new conv_op_t );
    // TODO/NOTE: non-square (_w/_h) handling is untested
    // SIGH: three cases are not quite consistent enough to be worth folding/sharing things more?
    if( !(cp.has_pad_w() || cp.has_pad_h()) ){ 
      u32_pt_t const p( cp.pad(), cp.pad() ); conv_op->in_pad = u32_box_t(p,p);
    } else { assert_st( cp.has_pad_w() && cp.has_pad_h() && (!cp.has_pad()) );
      u32_pt_t const p( cp.pad_w(), cp.pad_h() ); conv_op->in_pad = u32_box_t(p,p); 
    }
    if( !(cp.has_stride_w() || cp.has_stride_h()) ){ 
      conv_op->stride = u32_pt_t( cp.stride(), cp.stride() );
    } else { assert_st( cp.has_stride_w() && cp.has_stride_h() && (!cp.has_stride()) );
      conv_op->stride = u32_pt_t( cp.stride_w(), cp.stride_h() );
    }
    if( !(cp.has_kernel_w() || cp.has_kernel_h()) ){ 
      conv_op->kern_sz = u32_pt_t( cp.kernel_size(), cp.kernel_size() );
    } else { assert_st( cp.has_kernel_w() && cp.has_kernel_h() && (!cp.has_kernel_size()) );
      conv_op->kern_sz = u32_pt_t( cp.kernel_w(), cp.kernel_h() );
    }
    return conv_op;
  }
  template p_conv_op_t get_conv_op_from_param< caffe::ConvolutionParameter >( caffe::ConvolutionParameter const & cp );
  template p_conv_op_t get_conv_op_from_param< caffe::PoolingParameter >( caffe::PoolingParameter const & cp );

  p_conv_op_t make_p_conv_op_t_init_and_check_unused_from_lexp( p_lexp_t const & lexp, nesi_init_arg_t * const nia );

#define RF_TO_VEC( V, RF ) { for( int32_t i = 0; i != RF##_size(); ++i ) { V.push_back( RF(i) ); } }

  p_conv_pipe_t create_pipe_from_param( caffe::NetParameter & net_param, string const & out_layer_name ) { 
    // note: we only handle a (very) limited set of possible layers/networks here.
    p_conv_pipe_t conv_pipe( new conv_pipe_t );
    //vect_string const & layer_names = net->layer_names();
    bool found_layer = out_layer_name.empty(); // if no layer name input, don't try to find a 'stopping/end' layer
    for( int32_t i = 0; i != net_param.layer_size(); ++i ) { 
      caffe::LayerParameter const & lp = net_param.layer(i);
      assert_st( lp.has_name() );
      assert_st( lp.has_type() );
      p_conv_op_t conv_op;
      if( 0 ) {
      } else if( lp.type() == Convolution_str ) {
	assert_st( lp.has_convolution_param() );
	caffe::ConvolutionParameter const & cp = lp.convolution_param();
	conv_op = get_conv_op_from_param( cp );
	assert_st( cp.num_output() >= 0 ); // should zero be allowed?
	conv_op->out_chans = cp.num_output();
      } else if( (lp.type() == ReLU_str) || (lp.type() == Dropout_str) ) {
	// in-place layers to mostly-ignore
	conv_op.reset( new conv_op_t );
	conv_op->stride = {1,1}; // sensible, but currently unused
	conv_op->out_chans = 0; // no effect on chans
      } else if( lp.type() == LRN_str ) {
	//assert_st( lp.has_lrn_param() );
	//caffe::LRNParameter const & p = lp.lrn_param();	
	conv_op.reset( new conv_op_t );
	conv_op->stride = {1,1};
	conv_op->out_chans = 0; // no effect on chans
      } else if( lp.type() == Pooling_str ) {
	assert_st( lp.has_pooling_param() );
	caffe::PoolingParameter const & pp = lp.pooling_param();
	conv_op = get_conv_op_from_param( pp );
	conv_op->out_chans = 0; // no effect on chans
	// global pooling iff kernel size is all zeros (we use as a special value)
	assert_st( conv_op->kern_sz.is_zeros() == pp.global_pooling() ); 
      } else if( lp.type() == InnerProduct_str ) {
	assert_st( lp.has_inner_product_param() );
	caffe::InnerProductParameter const & ipp = lp.inner_product_param();
	conv_op.reset( new conv_op_t );
	conv_op->stride = {1,1};
	conv_op->out_chans = ipp.num_output();
      } else if( (lp.type() == Data_str) || (lp.type() == SoftmaxWithLoss_str) || (lp.type() == Accuracy_str) ) {
	// for now, just silently ignore data, softmax, acc layers. we'd need to handle phase issues to deal with them anyway
      } else if( lp.type() == Concat_str ) {
	conv_op.reset( new conv_op_t );
	conv_op->stride = {1,1};
	conv_op->out_chans = 0; // no effect on chans
      } else {
	printf( "warning: ignoring layer with lp.type()=%s\n", str(lp.type()).c_str() );
      }
      if( conv_op ) { 
	conv_op->tag = lp.name();
	conv_op->type = lp.type();
	RF_TO_VEC( conv_op->bots, lp.bottom );
	RF_TO_VEC( conv_op->tops, lp.top );
	// FIXME: handle ReLU / Dropout. for now, just check that they are one-in-one-out inplace
	if( (conv_op->type == "ReLU") || (conv_op->type == "Dropout") ) { 
	  assert_st( conv_op->bots.size() == 1 ); assert_st( conv_op->tops == conv_op->bots );
	  conv_pipe->get_or_make_node(conv_op->bots[0])->in_place_ops.push_back( conv_op->type );
	}
	else { conv_pipe->add_conv( conv_op ); }
      }
      if( (!found_layer) && (out_layer_name == lp.name()) ) { found_layer = 1; break; }
    }
    if( !found_layer ) { rt_err( strprintf("layer out_layer_name=%s not found in network\n",str(out_layer_name).c_str() )); }
    conv_pipe->finalize();
    conv_pipe->calc_support_info(1);
    return conv_pipe;
  }
}
