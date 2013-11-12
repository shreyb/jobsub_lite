#!/usr/bin/env python

################################################################################
# Project:
#   JobSub
#
# Author:
#   Parag Mhashilkar
#
# Description:
#   This module implements the JobSub client tool
#
################################################################################

import sys
import os
import getopt
import optparse

import constants
from jobsubClient import JobSubClient

def usage():
    print "%s <arg1> <arg2> <...>" % os.path.basename(sys.argv[0])
    print "Example: %s ..." % os.path.basename(sys.argv[0])


def required_args_present(options):
    try:
        if (options.acctGroup and options.jobsubServer):
            return True
    except AttributeError:
        return False
    return False


def print_opts(options):
    print '--------------------------------------------------------------------'
    print '%s' % options
    print '--------------------------------------------------------------------'


def parse_server_args(option, opt_str, value, parser):
     assert value is None
     value = []

     def floatable(str):
         try:
             float(str)
             return True
         except ValueError:
             return False

     for arg in parser.rargs:
         ## stop on --foo like options
         #if arg[:2] == "--" and len(arg) > 2:
         #    break
         ## stop on -a, but not on -3 or -3.0
         #if arg[:1] == "-" and len(arg) > 1 and not floatable(arg):
         #    break
         value.append(arg)

     del parser.rargs[:len(value)]
     setattr(parser.values, option.dest, value)


def parse_opts(argv):
    parser = optparse.OptionParser(usage='%prog [options]',
                                   version='v0.1',
                                   conflict_handler="resolve")

    # Required args
    parser.add_option('--acct-group',
                      dest='acctGroup',
                      action='store',
                      metavar='<AccountingGroup/Experiment>',
                      help='Accounting Group/Experiment name')

    # Optional args
    parser.add_option('--jobsub-server',
                      dest='jobsubServer',
                      action='store',
                      metavar='<JobSub Server>',
                      default=constants.JOBSUB_SERVER,
                      help='Alternate location of JobSub server to use')

    # Random server args
    parser.add_option('--jobsub-server-args',
                      dest='serverArgs',
                      action='callback',
                      callback=parse_server_args)
    if len(argv) < 1:
        print "ERROR: Insufficient arguments specified"
        parser.print_help()
        sys.exit(1)

    options, remainder = parser.parse_args(argv)

    #if len(remainder) > 1:
    #    parser.print_help(file)

    if not required_args_present(options):
        print "ERROR: Missing required arguments"
        parser.print_help()
        sys.exit(1)
    return options


def main(argv):
    options = parse_opts(argv)
    #print_opts(options)
    js_client = JobSubClient(options.jobsubServer,
                             options.serverArgs,
                             options.acctGroup)
    js_client.submit()

if __name__ == '__main__':
    main(sys.argv)
