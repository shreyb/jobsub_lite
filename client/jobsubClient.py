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
import base64
import pycurl
import urllib
import cStringIO
import platform
import json

import constants


class JobSubClient:

    def __init__(self, server, server_args, acct_group,
            job_exe, job_args, server_version='current'):
        self.server = server
        self.serverVersion = server_version
        self.serverArgs = server_args
        self.acctGroup = acct_group
        self.jobExe = job_exe
        self.jobArgs = job_args
        self.serverArgs_b64en = base64.urlsafe_b64encode('%s @%s %s' % (
            ' '.join(self.serverArgs), self.jobExe, self.jobArgs))
        #self.submitURL = constants.JOBSUB_JOB_SUBMIT_URL_PATTERN % (
        #                     self.server, self.serverVersion, self.acctGroup
        #                 )
        self.submitURL = constants.JOBSUB_JOB_SUBMIT_URL_PATTERN % (
                             self.server, self.acctGroup
                         )


    def submit(self):
        print 'URL: %s %s' % (self.submitURL, self.serverArgs_b64en)

        # Reponse from executing curl
        response = cStringIO.StringIO()

        # curl -cert /tmp/x509up_u501 -k -X POST -d -jobsub_args_base64=$COMMAND https://fcint076.fnal.gov:8443/jobsub/experiments/1/jobs/ 

        post_data = [
            ('jobsub_args_base64', self.serverArgs_b64en)
        ]
        creds = get_client_cert()
        print "CREDENTIALS: %s" % creds
        print '%s' % self.submitURL

        #cmd = 'curl -k -X POST -d jobsub_args_base64=%s %s' % (self.serverArgs_b64en, self.submitURL)
        #print 'EXECUTING: %s' % cmd
        #os.system(cmd)

        #sys.exit(0)
        # Create curl object and set curl options to use
        curl = pycurl.Curl()
        curl.setopt(curl.URL, self.submitURL)
        curl.setopt(curl.POST, True) # -X POST
        curl.setopt(curl.SSL_VERIFYHOST, True)
        curl.setopt(curl.FAILONERROR, True)
        curl.setopt(curl.TIMEOUT, constants.JOBSUB_PYCURL_TIMEOUT)
        curl.setopt(curl.CONNECTTIMEOUT, constants.JOBSUB_PYCURL_CONNECTTIMEOUT)
        curl.setopt(curl.FAILONERROR, True)
        curl.setopt(curl.SSLCERT, creds.get('cert'))
        curl.setopt(curl.SSLKEY, creds.get('key'))
        if platform.system() == 'Darwin':
            curl.setopt(curl.CAINFO, './ca-bundle.crt')
        else:
            curl.setopt(curl.CAPATH, get_capath())
        curl.setopt(curl.WRITEFUNCTION, response.write)
        curl.setopt(curl.HTTPHEADER, ['Accept: application/json'])

        f = None
        if self.jobExe:
            post_data.append(('jobsub_command', (pycurl.FORM_FILE, self.jobExe)))
        #curl.setopt(curl.POSTFIELDS, urllib.urlencode(post_fields))
        curl.setopt(curl.HTTPPOST, post_data)
        curl.perform()
        response_code = curl.getinfo(pycurl.RESPONSE_CODE)
        response_content_type = curl.getinfo(pycurl.CONTENT_TYPE)
        curl.close()

        if f:
            f.close()

        if response_code == 200:
            if response_content_type == 'application/json':
                response_dict = json.loads(response.getvalue())
                response_err = response_dict.get('err')
                response_out = response_dict.get('out')
                print_formatted_response(response_out)
                print_formatted_response(response_err, msg_type='ERROR')
            else:
                print_formatted_response(response.getvalue())
        else:
            print "Server response code: %s" % response_code
        response.close()



def print_formatted_response(msg, msg_type='OUTPUT'):
    print 'Response %s:' % msg_type
    if isinstance(msg, (str, int, float)):
        print '%s' % msg
    elif isinstance(msg, (list, tuple)):
        print '%s' % ' '.join(msg)

def get_client_cert():
    creds = {}
    cert = None
    key = None
    default_proxy = '/tmp/x509up_u%s' % os.getuid()

    if os.environ.get('X509_USER_PROXY'):
        cert = os.environ.get('X509_USER_PROXY')
        key = os.environ.get('X509_USER_PROXY')
    elif (os.environ.get('X509_USER_CERT') and os.environ.get('X509_USER_KEY')):
        cert = os.environ.get('X509_USER_CERT')
        key = os.environ.get('X509_USER_KEY')
    elif os.path.exists(default_proxy):
        cert = key = default_proxy
    else:
        raise('Cannot find credentials to use')

    return {'cert': cert, 'key': key}

def get_capath():
    system_ca_dir = '/etc/grid-security/certificates'
    ca_dir = None
    ca_dir = os.environ.get('X509_CERT_DIR')

    if (not ca_dir) and (os.path.exists(system_ca_dir)):
        ca_dir = system_ca_dir
    if not ca_dir:
        raise('Could not find CA Certificates. Set X509_CA_DIR')

    print 'Using CA_DIR: %s' % ca_dir
    return ca_dir
