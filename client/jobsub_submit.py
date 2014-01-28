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
from jobsubClient import JobSubClientSubmissionError


def split_client_server_args(parser, argv):
    cli_argv = [argv[0]]
    srv_argv = []

    i = 1
    while (i < len(sys.argv)):

        opt = parser.get_option(argv[i])

        if opt:
            cli_argv.append(argv[i])
            if opt.action in optparse.Option.TYPED_ACTIONS:
                try:
                    cli_argv.append(argv[i+1])
                    i += 1
                except IndexError:
                    parser.error('%s option requires an argument' % argv[i])
        elif '=' in argv[i]:
            # Check if the arg splitter is '=' example --foo=bar
            opt = parser.get_option(argv[i].split('=')[0])
            if opt:
                cli_argv.append(argv[i])
            else:
                srv_argv.append(argv[i])
        else:
            srv_argv.append(argv[i])

        i += 1

    return (cli_argv, srv_argv)


def required_args_present(options):
    try:
        if (options.acctGroup and options.jobsubServer):
            return True
    except AttributeError:
        return False
    return False


def print_opts(options):
    logSupport.dprint('------------------------------------------------------')
    logSupport.dprint('%s' % options)
    logSupport.dprint('------------------------------------------------------')


"""
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
"""

def parse_opts(argv):
    parser = optparse.OptionParser(usage='%prog [options]',
                                   version='v0.1',
                                   conflict_handler="resolve")

    # Required args
    parser.add_option('-G', '--group',
                      dest='acctGroup',
                      type='string',
                      action='store',
                      metavar='<Group/Experiment/Subgroup>',
                      help='Group/Experiment/Subgroup for priorities and accounting')

    # Optional args
    parser.add_option('--jobsub-server',
                      dest='jobsubServer',
                      action='store',
                      metavar='<JobSub Server>',
                      default=constants.JOBSUB_SERVER,
                      help='Alternate location of JobSub server to use')

    parser.add_option('--debug',
                      dest='debug',
                      action='store_true',
                      default=False,
                      help='Print debug messages to stdout')

    if len(argv) < 1:
        print "ERROR: Insufficient arguments specified"
        parser.print_help()
        sys.exit(1)

    cli_argv, srv_argv = split_client_server_args(parser, argv)

    options, remainder = parser.parse_args(cli_argv)

    if len(remainder) > 1:
        parser.print_help(file)

    if not required_args_present(options):
        print "ERROR: Missing required arguments"
        parser.print_help()
        sys.exit(1)
    return (options, srv_argv)


def main(argv):
    options, srv_argv = parse_opts(argv)
    logSupport.init_logging(options.debug)
    logSupport.dprint('SERVER_ARGS: ', srv_argv)
    logSupport.dprint('CLIENT_ARGS: ', options)
    js_client = JobSubClient(options.jobsubServer, options.acctGroup, srv_argv)
    try:
        stime = time.time()
        js_client.submit()
        etime = time.time()
        print 'Remote Submission Processing Time: %s sec' % (etime - stime)
    except JobSubClientSubmissionError, e:
        print e
        logSupport.dprint(traceback.format_exc())
        return 1
    except Exception, e:
        print e
        logSupport.dprint('%s' % traceback.print_exc())
        return 1

if __name__ == '__main__':
    sys.exit(main(sys.argv))

# TO TEST RUN SOMETHING LIKE THE FOLLOWING

# X509_CERT_DIR=/Users/parag/.globus/certificates X509_USER_CERT=/Users/parag/.globus/x509up_u11017 X509_USER_KEY=/Users/parag/.globus/x509up_u11017 ./jobsub.py --group nova --jobsub-server https://fermicloud326.fnal.gov:8443 -g -N 3 --site Fermicloud-MultiSlots parag_test.sh --job-args 100

### Following are old examples
# X509_CERT_DIR=/Users/parag/.globus/certificates X509_USER_CERT=/Users/parag/.globus/x509up_u11017 X509_USER_KEY=/Users/parag/.globus/x509up_u11017 ./jobsub.py --acct-group 1 --jobsub-server https://fermicloud326.fnal.gov:8443 --job-exe parag_test.sh --job-args 100 --jobsub-server-args -g -N 3 --site Fermicloud-MultiSlots
#X509_CERT_DIR=/Users/parag/.globus/certificates X509_USER_CERT=/Users/parag/.globus/x509up_u11017 X509_USER_KEY=/Users/parag/.globus/x509up_u11017 ./jobsub.py --acct-group 1 --jobsub-server https://fermicloud326.fnal.gov:8443 --jobsub-server-args -g -N 3 --site Fermicloud-MultiSlots --X509_USER_PROXY=/scratch/proxies/dbox/dbox.nova.proxy /scratch/app/users/condor-exec/dbox/test_grid_env.sh 100
