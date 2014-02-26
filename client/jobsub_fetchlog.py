#!/usr/bin/env python

import os
import sys
import json
import optparse
import pycurl
import time
import platform
import email

import constants
from jobsubClient import get_capath, get_client_credentials, print_formatted_response


def required_args_present(options):
    try:
        if options.acctGroup and options.jobsubServer and options.jobId:
            return True
    except AttributeError:
        return False
    return False


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

    parser.add_option('-J', '--job',
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
                      default=constants.JOBSUB_SERVER,
                      help='Alternate location of JobSub server to use')

    if len(argv) < 1:
        print "ERROR: Insufficient arguments specified"
        parser.print_help()
        sys.exit(1)

    options, remainder = parser.parse_args(argv)

    if len(remainder) > 1:
        parser.print_help(file)

    if not required_args_present(options):
        print "ERROR: Missing required arguments"
        parser.print_help()
        sys.exit(1)

    return options


def decode_multipart_formdata(infile):
    msg = email.message_from_file(infile)

    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get_content_type() == 'application/json':
            response_dict = json.loads(part.get_payload(decode=True))
            print_formatted_response('JobStatus: %s' % response_dict.get('job_status'))
        elif part.get_content_type() == 'application/zip':
            filename = 'out_' + part.get_filename()
            with open(filename, 'wb') as fp:
                fp.write(part.get_payload(decode=True))
                print 'Downloaded to %s' % filename


def get_sandbox(options):
    creds = get_client_credentials()
    submitURL = constants.JOBSUB_JOB_SANDBOX_URL_PATTERN % (options.jobsubServer, options.acctGroup, options.jobId)

    print
    print 'CREDENTIALS    : %s\n' % creds
    print 'SUBMIT_URL     : %s\n' % submitURL

    fn = '%s.encoded' % options.jobId
    fp = open(fn, 'wb')
    # Create curl object and set curl options to use
    curl = pycurl.Curl()
    curl.setopt(curl.URL, submitURL)
    curl.setopt(curl.WRITEFUNCTION, fp.write)
    curl.setopt(curl.SSL_VERIFYHOST, True)
    curl.setopt(curl.FAILONERROR, False)
    curl.setopt(curl.TIMEOUT, constants.JOBSUB_PYCURL_TIMEOUT)
    curl.setopt(curl.CONNECTTIMEOUT, constants.JOBSUB_PYCURL_CONNECTTIMEOUT)
    curl.setopt(curl.SSLCERT, creds.get('cert'))
    curl.setopt(curl.SSLKEY, creds.get('key'))
    if platform.system() == 'Darwin':
        curl.setopt(curl.CAINFO, './ca-bundle.crt')
    else:
        curl.setopt(curl.CAPATH, get_capath())
    curl.setopt(curl.HTTPHEADER, ['Accept: multipart/alternative,application/json'])

    curl.perform()
    response_code = curl.getinfo(pycurl.RESPONSE_CODE)
    response_content_type = curl.getinfo(pycurl.CONTENT_TYPE)
    curl.close()
    fp.close()

    if response_code == 200:
        with open(fn, 'rb') as infile:
            decode_multipart_formdata(infile)
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
