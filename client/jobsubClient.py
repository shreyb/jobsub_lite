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
from StringIO import StringIO

import constants


class JobSubClient:

    def __init__(self, server, server_args, acct_group, server_version='current'):
        self.server = server
        self.serverVersion = 'current'
        self.serverArgs = server_args
        self.acctGroup = acct_group
        self.serverArgs_b64en = base64.urlsafe_b64encode(' '.join(self.serverArgs))
        #self.submitURL = constants.JOBSUB_JOB_SUBMIT_URL_PATTERN % (
        #                     self.server, self.serverVersion, self.acctGroup
        #                 )
        self.submitURL = constants.JOBSUB_JOB_SUBMIT_URL_PATTERN % (
                             self.server, self.acctGroup
                         )


    def submit(self):
        print '%s %s' % (self.submitURL, self.serverArgs_b64en)

        # Reponse from executing curl
        response = StringIO()

        # curl -cert /tmp/x509up_u501 -k -X POST -d -jobsub_args_base64=$COMMAND https://fcint076.fnal.gov:8443/jobsub/experiments/1/jobs/ 

        post_data = {'jobsub_args_base64': self.serverArgs_b64en}
        creds = get_client_cert()
        print "Using credentials: %s" % creds
        print '%s' % self.submitURL

        cmd = 'curl -k -X POST -d jobsub_args_base64=%s %s' % (self.serverArgs_b64en, self.submitURL)
        print 'EXECUTING: %s' % cmd

        os.system(cmd)


        sys.exit(0)
        # Create curl object and set curl options to use
        curl = pycurl.Curl()
        curl.setopt(curl.URL, self.submitURL)
        curl.setopt(curl.POST, 1) # -X POST
        curl.setopt(curl.SSL_VERIFYHOST, 0)
        #curl.setopt(curl.POSTFIELDS, post_data)
        curl.setopt(curl.POSTFIELDS, urllib.urlencode(post_data))
        #curl.setopt(curl.SSLCERT, creds.get('cert'))
        #curl.setopt(curl.SSLKEY, creds.get('key'))
        curl.setopt(curl.WRITEFUNCTION, response.write)

        curl.perform()
        curl.close()

        while (not response.close()):
            print 'Waiting ...'
        print '%s' % response.readlines()


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
