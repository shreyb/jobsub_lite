#!/usr/bin/env python

import sys
import optparse
import pycurl
import time
import platform
import json
import os
import errno
import zipfile
import tarfile
import shutil

from defaultServer import defaultServer

import constants
from jobsubClient import get_capath, get_client_credentials, print_formatted_response, force_refresh


def required_args_present(options):
    try:
        if options.acctGroup and options.jobsubServer and options.jobId:
            return True
    except AttributeError:
        return False
    return False


def parse_opts(argv):
    parser = optparse.OptionParser(usage='%prog [options]',
                                   version='v0.2',
                                   conflict_handler="resolve")

    # Required args
    parser.add_option('-G', '--group',
                      dest='acctGroup',
                      type='string',
                      action='store',
                      metavar='<Group/Experiment/Subgroup>',
                      help='Group/Experiment/Subgroup for priorities and accounting')

    parser.add_option('-J', '--job','--jobid',
                      dest='jobId',
                      type='string',
                      action='store',
                      metavar='<Job ID>',
                      help='Job ID')

    # Optional args
    parser.add_option('--jobsub-server',
                      dest='jobsubServer',
                      action='store',
                      metavar='<JobSub Server>',
                      default=defaultServer(),
                      help='Alternate location of JobSub server to use')

    parser.add_option('--timeout',
                      dest='timeout',
                      type='int',
                      action='store',
                      metavar='<Timeout>',
                      default=None,
                      help='Timeout for the operation in sec')

    parser.add_option('--unzipdir',
                      dest='unzipdir',
                      type='string',
                      action='store',
                      metavar='<Unzip Dir>',
                      default=None,
                      help='Directory to automatically unzip logs into')

    parser.add_option('--archive-format',
                      dest='format',
                      type='string',
                      action='store',
                      metavar='<Archive Format>',
                      default='tar',
                      help='format for downloaded archive:"tar" (default,compressed) or "zip"')


    if len(argv) < 1:
        print "ERROR: Insufficient arguments specified"
        parser.print_help()
        sys.exit(1)

    options, remainder = parser.parse_args(argv)

    if len(remainder) > 1:
        #parser.print_help(file)
        parser.print_help()

    if not required_args_present(options):
        print "ERROR: Missing required arguments"
        parser.print_help()
        sys.exit(1)

    return options

def checkUnzipDir(unzipDir):
    if not unzipDir:
        return
    try:
        os.makedirs(unzipDir)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def get_sandbox(options):
    creds = get_client_credentials()
    if options.jobId.find('@')>0:
        job,mach=options.jobId.split('@')
        options.jobsubServer="https://%s:8443"%mach
        #options.jobId=job
    submitURL = constants.JOBSUB_JOB_SANDBOX_URL_PATTERN % (options.jobsubServer, options.acctGroup, options.jobId)
    if options.format=='zip':
        submitURL="%s?archive_format=zip"%(submitURL)

    checkUnzipDir( options.unzipdir )
    force_refresh()

    print
    print 'CREDENTIALS    : %s\n' % creds
    print 'SUBMIT_URL     : %s\n' % submitURL

    if options.format=='zip':
        fn = '%s.zip' % options.jobId
    else:
        fn = '%s.tgz' % options.jobId

    fp = open(fn, 'w')
    # Create curl object and set curl options to use
    curl = pycurl.Curl()
    curl.setopt(curl.URL, submitURL)
    curl.setopt(curl.WRITEFUNCTION, fp.write)
    curl.setopt(curl.SSL_VERIFYHOST, 0)
    curl.setopt(curl.FAILONERROR, False)
    timeout = constants.JOBSUB_PYCURL_TIMEOUT
    if options.timeout:
        timeout = options.timeout
    curl.setopt(curl.TIMEOUT, timeout)
    curl.setopt(curl.CONNECTTIMEOUT, constants.JOBSUB_PYCURL_CONNECTTIMEOUT)
    curl.setopt(curl.SSLCERT, creds.get('cert'))
    curl.setopt(curl.SSLKEY, creds.get('key'))
    if platform.system() == 'Darwin':
        curl.setopt(curl.CAINFO, './ca-bundle.crt')
    else:
        curl.setopt(curl.CAPATH, get_capath())
    curl.setopt(curl.HTTPHEADER, ['Accept: application/x-download,application/json'])

    curl.perform()
    response_code = curl.getinfo(pycurl.RESPONSE_CODE)
    response_content_type = curl.getinfo(pycurl.CONTENT_TYPE)
    curl.close()
    fp.close()

    if response_code == 200:
        print 'Downloaded to %s' % fn
        if options.unzipdir is not None:
            print "Moved files to %s"%options.unzipdir
            if options.format=='zip':
                z=zipfile.ZipFile(fn)
                z.extractall(options.unzipdir)
                d=''
                for f in z.namelist():
                    b=os.path.basename(f)
                    s=os.path.join(options.unzipdir,f)
                    d=os.path.dirname(s)
                    t=os.path.join(options.unzipdir,b)
                    shutil.move(s,t)
                os.rmdir(d)
            else:
                t=tarfile.open(fn)
                t.extractall(options.unzipdir)
                t.close()
            os.remove(fn)

    elif response_code == 404:
        with open(fn, 'r') as fp:
            value = fp.read()
            if response_content_type == 'application/json':
                response_dict = json.loads(value)
                response_err = response_dict.get('err')
                response_out = response_dict.get('out')
                print_formatted_response(response_out)
                print_formatted_response(response_err, msg_type='ERROR')
            else:
                print_formatted_response(value)
        os.remove(fn)


def main(argv):
    options = parse_opts(argv)
    stime = time.time()
    get_sandbox(options)
    etime = time.time()
    print 'Remote Submission Processing Time: %s sec' % (etime - stime)


if __name__ == '__main__':
    main(sys.argv)
