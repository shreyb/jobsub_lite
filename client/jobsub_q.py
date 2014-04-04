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
import time
import traceback

import constants
import logSupport
from jobsubClient import JobSubClient
from jobsubClient import JobSubClientError

def print_opts(options):
    logSupport.dprint('COMMAND LINE OPTIONS:')
    logSupport.dprint('%s' % options)


def required_args_present(options):
    try:
        if options.acctGroup and options.jobsubServer :
            return True
    except AttributeError:
        return False
    return False


def parse_opts(argv):
    usage = '%prog [Client Options]'
    parser = optparse.OptionParser(usage=usage,
                                   conflict_handler="resolve")

    opt_group = optparse.OptionGroup(parser, "Client Options")

    # Required args
    opt_group.add_option('-G', '--group',
                         dest='acctGroup',
                         type='string',
                         action='store',
                         metavar='<Group/Experiment/Subgroup>',
                         help='Group/Experiment/Subgroup for priorities and accounting')

    # Optional args
    opt_group.add_option('--jobsub-server',
                         dest='jobsubServer',
                         action='store',
                         metavar='<JobSub Server>',
                         default=constants.JOBSUB_SERVER,
                         help='Alternate location of JobSub server to use')

    opt_group.add_option('--role',
                         dest='acctRole',
                         type='string',
                         action='store',
                         metavar='<VOMS Role>',
                         default=None,
                         help='VOMS Role for priorities and accounting')

    opt_group.add_option('--jobid',
                         dest='jobId',
                         type='string',
                         action='store',
                         metavar='<Job ID>',
                         default=None,
                         help='Job Id (Cluster ID)  to query')

    opt_group.add_option('--debug',
                         dest='debug',
                         action='store_true',
                         default=False,
                         help='Print debug messages to stdout')

    opt_group.add_option('-h', '--help',
                         dest='help',
                         action='store_true',
                         default=False,
                         help='Show this help message and exit')

    parser.add_option_group(opt_group)

    if len(argv) < 1:
        print "ERROR: Insufficient arguments specified"
        parser.print_help()
        sys.exit(1)

    options, remainder = parser.parse_args(argv)

    if options.help or (len(remainder) > 1):
        parser.print_help()
        sys.exit(0)

    if not required_args_present(options):
        print "ERROR: Missing required arguments"
        parser.print_help()
        sys.exit(1)
    return options


def main(argv):
    options = parse_opts(argv)
    logSupport.init_logging(options.debug)
    logSupport.dprint('CLIENT_ARGS: ', options)
    #js_client = JobSubClient(options.jobsubServer, options.acctGroup,
    #                         options.acctRole)
    js_client = JobSubClient(options.jobsubServer, options.acctGroup, None, [])
    try:
            stime = time.time()
            js_client.list(options.jobId)
            etime = time.time()
            print 'Remote Listing Processing Time: %s sec' % (etime - stime)
    except JobSubClientError, e:
        print e
        logSupport.dprint(traceback.format_exc())
        return 1
    except Exception, e:
        print e
        logSupport.dprint('%s' % traceback.print_exc())
        return 1

if __name__ == '__main__':
    sys.exit(main(sys.argv))
