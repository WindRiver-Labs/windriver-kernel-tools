#!/usr/bin/env python

# Kconfig symbol analsysis
#
# Copyright (C) 2016 Bruce Ashfield
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

## example:
##     KERNELVERSION=4.7-rc5 SRCARCH=x86 ARCH=x86 ./Kconfiglib/examples/symbol_why.py

import sys
import os

# Kconfiglib should be installed into an existing python library
# location OR a path to where the library is should be set via something
# like: PYTHONPATH="./Kconfiglib:$PYTHONPATH".
#
# But if neither of those are true, let's try and find it ourselves
#
pathname = os.path.dirname(sys.argv[0])
try:
    import kconfiglib
except ImportError:
    sys.path.append( pathname + '/Kconfiglib')
    try:
        import kconfiglib
    except ImportError:
        raise ImportError('Could not import kconfiglib, make sure it is properly installed')

import argparse
import re
import os

dotconfig = ''
ksrc = ''
verbose = ''
show_summary = False
show_vars = False
show_selected = False
show_prompt = False
show_conditions = False
show_value = False

parser = argparse.ArgumentParser(
                formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                description="Kconfig symbol determination")

parser.add_argument("-c", "--dotconfig",
                    help="path to the .config to load")
parser.add_argument("-s", "--ksrc",
                    help="path to the kernel source")
parser.add_argument("-v", action='store_true',
                    help="verbose")
parser.add_argument("--summary", action='store_true',
                    help="Show variable summary")
parser.add_argument("--prompt", action='store_true',
                    help="Show variable prompt")
parser.add_argument("--conditions", action='store_true',
                    help="Show config option dependencies" )
parser.add_argument("--vars", action='store_true',
                    help="Show the dependent variables" )
parser.add_argument("--value", action='store_true',
                    help="Show the config value" )
parser.add_argument("config", help="configuration option to check")
parser.add_argument('args', help="<path to .config> <path to kernel source tree>", nargs=argparse.REMAINDER)

args, unknownargs = parser.parse_known_args()

# pull these out of args, since we want to test the variables .. and they
# can bet set by more than the command line
if args.dotconfig:
    dotconfig=args.dotconfig
if args.ksrc:
    ksrc=args.ksrc
if args.v:
    verbose=True
if args.config:
    option=args.config
if args.summary:
    show_summary=args.summary
if args.prompt:
    show_prompt=args.prompt
if args.conditions:
    show_conditions=args.conditions
if args.vars:
    show_vars=args.vars
if args.value:
    show_value=args.value

# a little extra processing, since argparse will stop at the first non
# dashed option. We take whatever is left over, check to see if all our
# options are defined .. and if they aren't we use these ones.
for opt in args.args:
    if opt == '-h' or opt == "--help":
        parser.print_help()
        sys.exit()
    elif opt == '-v':
        verbose=1
    elif opt == '--summary':
        show_summary=True
    elif opt == '--conditions':
        show_conditions=True
    elif opt == '--prompt':
        show_prompt=True
    elif opt == '--vars':
        show_vars=True
    elif opt == '--value':
        show_value=True
    elif re.match( "--dotconfig=*", opt):
        temp, dotconfig = opt.split('=', 2)
    elif re.match( "--ksrc=*", opt):
        temp, ksrc = opt.split('=', 2)
    else:
        if re.match( ".*\.config", opt ):
            dotconfig=opt
        elif not ksrc:
            ksrc=opt

if not os.path.exists( dotconfig ):
    print( "ERROR: .config '%s' does not exist" % dotconfig )
    sys.exit(1)

# There are three required environment variables:
#  - KERNELVERSION
#  - SRCARCH
#  - ARCH
#
# If SRCARCH isn't set, but ARCH is, we simply make SRCARCH=ARCH, but
# other missing variables are an error
#
if not os.getenv("KERNELVERSION"):
    hconfig = open( dotconfig )
    for line in hconfig:
        line = line.rstrip()
        x = re.match( "^# .*Linux/\w*\s*([0-9]*\.[0-9]*\.[0-9]*).*Kernel Configuration", line )
        if x:
            os.environ["KERNELVERSION"] = x.group(1)
            if verbose:
                print( "[INFO]: kernel version %s found in .config, if this is incorrect, set KERNELVERSION in the environement" % x.group(1) )

    if not os.getenv("KERNELVERSION"):
        os.environ["KERNELVERSION"] = "4.7"
        if verbose:
            print( "[INFO]: default kernel version 4.7 used, if this is incorrect, set KERNELVERSION in the environement" )

if not os.getenv("SRCARCH"):
    if os.getenv("ARCH"):
        os.environ["SRCARCH"] = os.getenv("ARCH")
    else:
        print( "ERROR: source arch must be set (via SRCARCH environment variable" )
        sys.exit(1)

if not os.getenv("ARCH"):
    print( "ERROR: arch must be set (via ARCH environment variable" )
    sys.exit(1)

if not ksrc:
    ksrc = "."

kconf = ksrc + "/Kconfig"
if not os.path.exists( kconf ):
    print( "ERROR: kernel source directory '%s' does not contain a top level Kconfig file" % ksrc )
    sys.exit(1)

if verbose:
    print( "[INFO]: dotconfig: " + dotconfig)
    print( "[INFO]: ksrc: " + ksrc )
    print( "[INFO]: option: " + option )
    print( "[INFO]: kernel ver: " + format(os.getenv("KERNELVERSION")) )
    print( "[INFO]: src arch: " + os.getenv("SRCARCH") )
    print( "[INFO]: arch: " + os.getenv("ARCH") )

# Create a Config object representing a Kconfig configuration. (Any number of
# these can be created -- the library has no global state.)
conf = kconfiglib.Config(kconf)

# Load values from a .config file.
conf.load_config( dotconfig )

opt = conf[option]

if show_summary:
    print(conf[option])

if show_vars:
    print( "" )
    print( "Variables that depend on '%s':" % option )

    for sym in conf:
        if opt in sym.get_referenced_symbols():
            print("    " + sym.get_name())

if show_prompt:
    print( "Prompt for '%s': %s" % (option,opt.get_prompts()) )

refs = opt.get_referenced_symbols()
selected = opt.get_selected_symbols()
if show_selected:
    for sel in selected:
        print( sel.get_name() )

if show_conditions:
    print("Config '%s' has the following conditionals: " % option )
    prompts_str_rows = []
    #for conditional, cond_expr in opt.orig_prompts:
    for val_expr, cond_expr in opt.orig_def_exprs:
        # row_str = conf._expr_val_str(val_expr, "(none)")
        # prompts_str_rows.append( row_str )
        prompts_str_rows.append( conf._expr_val_str(cond_expr) )

    for conditional, cond_expr in opt.orig_prompts:
        prompts_str_rows.append( conf._expr_val_str(cond_expr) )

    print "  " + '\n'.join(prompts_str_rows)

    # if it is a referenced variable, but not selected, then it is a dependency
    depends_string=""
    for s in refs:
        if not s in selected:
            depends_string += " " + s.get_name() + " [" + s.get_value() + "]"

    print( "Dependency values are: " )
    print( " %s" % depends_string )

if show_value:
    print( "Config '%s' has value: %s" % (option, opt.get_value()))
