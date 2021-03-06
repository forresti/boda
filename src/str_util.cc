// Copyright (c) 2013-2014, Matthew W. Moskewicz <moskewcz@alumni.princeton.edu>; part of Boda framework; see LICENSE
#include"boda_tu_base.H"
#include"str_util.H"
#include<stdarg.h>
#include<assert.h>
#include<malloc.h>
#include<boost/lexical_cast.hpp>
#include<boost/algorithm/string.hpp>

namespace boda
{
  using std::string;

  string get_part_before( string const & s, string const & to_find ) {
    size_t const ix = s.find( to_find );
    if( ix == string::npos ) { return s; }
    else { return string( s, 0, ix ); }
  }
  string get_part_after( string const & s, string const & to_find ) {
    size_t const ix = s.find( to_find );
    if( ix == string::npos ) { return string(); }
    else { return string( s, ix+to_find.size(), string::npos ); }
  }

  double lc_str_d( char const * const s )
  { 
    try { return boost::lexical_cast< double >( s ); }
    catch( boost::bad_lexical_cast & e ) { rt_err( strprintf("can't convert '%s' to double.", s ) ); }
  }
  uint32_t lc_str_u32( char const * const s )
  { 
    try { return boost::lexical_cast< uint32_t >( s ); }
    catch( boost::bad_lexical_cast & e ) { rt_err( strprintf("can't convert '%s' to uint32_t.", s ) ); }
  }
  double lc_str_d( string const & s ) { return lc_str_d( s.c_str() ); } 
  uint32_t lc_str_u32( string const & s ) { return lc_str_u32( s.c_str() ); } 

  string join( vect_string const & vs, string const & sep ) {
    string ret;
    for( vect_string::const_iterator i = vs.begin(); i != vs.end(); ++i ) {
      if( i != vs.begin() ) { ret += sep; }
      ret += *i;
    }
    return ret;
  }

  // note: not reversable (i.e. just sanitization, not escaping)
  string as_pyid_fixme( string const & s ) {
    string ret;
    for (string::const_iterator i = s.begin(); i != s.end(); ++i) {
      switch (*i) {
      case '-': ret += "_"; break;
      case '.': ret += "_"; break;
      default: ret.push_back( *i );
      }
    }
    return ret;
  }
  string as_py_str_list( vect_string const & vs ) { 
    vect_string vs_id;
    for( vect_string::const_iterator i = vs.begin(); i != vs.end(); ++i ) { vs_id.push_back( "\""+(*i)+"\"" ); }
    return "[ " + join(vs_id,", ") + " ]"; 
  }

  // size of return value is always 1 + (count of sep in s)
  vect_string split( std::string const & s, char const sep ) {
    vect_string ret;
    string::const_iterator b = s.begin();
    for( string::const_iterator i = s.begin(); i != s.end(); ++i) {
      if( (*i) == sep ) {
	ret.push_back( string( b, i ) );
	b = i+1;
      }
    }
    ret.push_back( string( b, s.end() ) );
    return ret;
  }

  vect_string split_ws( std::string const & s ) {
    vect_string parts;
    boost::algorithm::split( parts, s, boost::algorithm::is_space(), boost::algorithm::token_compress_on );
    return parts;
  }

  string strip_ws( std::string const & s ) { return boost::algorithm::trim_copy( s ); }


  string strprintf( char const * const format, ... )
  {
    va_list ap;
    char *s = 0;
    va_start( ap, format );
    int const va_ret = vasprintf( &s, format, ap );
    assert( va_ret > 0 );
    va_end( ap );
    assert( s );
    string ret( s );
    free(s);
    return ret;
  }

  // FIXME: factor out dupe junk around vasprintf() calls? can't do without ret more string copy overhead? hmm.
  filename_t filename_t_printf( filename_t const & fn, ... ) // note: can't use gcc format-string checking here
  {
    filename_t ret;
    va_list ap;
    char *s = 0;
    int va_ret = 0;

    va_start( ap, fn );
    va_ret = vasprintf( &s, fn.in.c_str(), ap );
    assert( va_ret > 0 );
    va_end( ap );
    assert( s );
    ret.in = string( s );
    free(s); s = 0; va_ret = 0;

    va_start( ap, fn );
    va_ret = vasprintf( &s, fn.exp.c_str(), ap );
    assert( va_ret > 0 );
    va_end( ap );
    assert( s );
    ret.exp = string( s );
    free(s); s = 0;

    return ret;
  }

  void printstr( string const & str )
  {
    printf( "%s", str.c_str() );
  }

  string replace_chars_with_char( string const & s, string const & chars_to_find, char const rep_with ) {
    string ret;
    for (string::const_iterator i = s.begin(); i != s.end(); ++i) {
      if( chars_to_find.find(*i) != string::npos ) { ret.push_back( rep_with ); }
      else { ret.push_back( *i ); }
    }
    return ret;
  }

  string xml_escape( string const & str )
  {
    string ret;
    for (string::const_iterator i = str.begin(); i != str.end(); ++i) {
      switch (*i)
      {
      case '&': ret += "&amp;"; break;
      case '<': ret += "&lt;"; break;
      case '>': ret += "&gt;"; break;
      case '"': ret += "&quot;"; break;
      default: ret.push_back( *i );
      }
    }
    return ret;
  }
}

