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
import re
import base64
import pycurl
import urllib
import cStringIO
import platform
import json
import copy
import traceback

import constants
import jobsubClientCredentials
import logSupport

class JobSubClientError(Exception):
    def __init__(self):
        Exception.__init__(self, "JobSub client action failed.")


class JobSubClientSubmissionError(Exception):
    def __init__(self):
        Exception.__init__(self, "JobSub remote submission failed.")


class JobSubClient:

    def __init__(self, server, acct_group, server_argv, dropboxServer=None, server_version='current'):
        self.server = server
        self.dropboxServer = dropboxServer
        self.serverVersion = server_version
        self.acctGroup = acct_group
        self.serverArgv = server_argv

        self.helpURL = constants.JOBSUB_ACCTGROUP_HELP_URL_PATTERN % (
                             self.server, self.acctGroup
                       )

        self.submitURL = constants.JOBSUB_JOB_SUBMIT_URL_PATTERN % (
                             self.server, self.acctGroup
                         )

        # PM: Following is specific to job submission and dropbox
        #     This should not be in the constructor 

        if self.serverArgv: 
            self.jobExeURI = get_jobexe_uri(self.serverArgv)
            self.jobExe = uri2path(self.jobExeURI)
            self.jobDropboxURIMap = get_dropbox_uri_map(self.serverArgv)
            self.serverEnvExports = get_server_env_exports(server_argv)

            srv_argv = copy.copy(server_argv)

            if self.jobDropboxURIMap:
                # upload the files
                result = self.dropbox_upload()
                # replace uri with path on server
                for idx in range(0, len(srv_argv)):
                    arg = srv_argv[idx]
                    if arg.startswith(constants.DROPBOX_SUPPORTED_URI):
                        key = self.jobDropboxURIMap.get(arg)
                        if key is not None:
                            values = result.get(key)
                            if values is not None:
                                if self.dropboxServer is None:
                                    srv_argv[idx] = values.get('path')
                                else:
                                    url = values.get('url')
                                    srv_argv[idx] = '%s%s' % (self.dropboxServer, url)
                            else:
                                print "Dropbox upload failed with error:"
                                print json.dumps(result)
                                raise JobSubClientSubmissionError


            if self.jobExeURI and self.jobExe:
                idx = get_jobexe_idx(srv_argv)
                if self.requiresFileUpload(self.jobExeURI):
                    srv_argv[idx] = '@%s' % self.jobExe

            if self.serverEnvExports:
                srv_env_export_b64en = base64.urlsafe_b64encode(self.serverEnvExports)
                srv_argv.insert(0, '--export_env=%s' % srv_env_export_b64en)

            self.serverArgs_b64en = base64.urlsafe_b64encode(' '.join(srv_argv))


    def dropbox_upload(self):
        result = dict()

        # Reponse from executing curl
        response = cStringIO.StringIO()

        post_data = list()
        creds = get_client_credentials()

        dropboxURL = constants.JOBSUB_DROPBOX_POST_URL_PATTERN % (self.dropboxServer or self.server, self.acctGroup)
        # Create curl object and set curl options to use
        curl = pycurl.Curl()
        curl.setopt(curl.URL, dropboxURL)
        curl.setopt(curl.POST, True)
        curl.setopt(curl.SSL_VERIFYHOST, constants.JOBSUB_SSL_VERIFYHOST)
        curl.setopt(curl.FAILONERROR, True)
        curl.setopt(curl.TIMEOUT, constants.JOBSUB_PYCURL_TIMEOUT)
        curl.setopt(curl.CONNECTTIMEOUT, constants.JOBSUB_PYCURL_CONNECTTIMEOUT)
        curl.setopt(curl.FAILONERROR, True)
        curl.setopt(curl.SSLCERT, creds.get('cert'))
        curl.setopt(curl.SSLKEY, creds.get('key'))
        curl.setopt(curl.CAPATH, get_capath())
        curl.setopt(curl.WRITEFUNCTION, response.write)
        curl.setopt(curl.HTTPHEADER, ['Accept: application/json'])

        # If it is a local file upload the file
        for file, key in self.jobDropboxURIMap.items():
            post_data.append((key, (pycurl.FORM_FILE, uri2path(file))))
        curl.setopt(curl.HTTPPOST, post_data)
        try:
            curl.perform()
        except pycurl.error, error:
            errno, errstr = error
            print "PyCurl Error %s: %s" % (errno, errstr)
            logSupport.dprint(traceback.format_exc())
            raise JobSubClientSubmissionError

        response_code = curl.getinfo(pycurl.RESPONSE_CODE)
        response_content_type = curl.getinfo(pycurl.CONTENT_TYPE)
        curl.close()

        print "Server response code: %s" % response_code
        if response_code == 200:
            value = response.getvalue()
            if response_content_type == 'application/json':
                result = json.loads(value)
            else:
                print_formatted_response(value)
        response.close()

        return result


    def remove(self, jobid):
        creds = get_client_credentials()
        self.removeURL = constants.JOBSUB_JOB_REMOVE_URL_PATTERN % (
                             self.server, self.acctGroup, jobid
                         )

        logSupport.dprint('REMOVE URL     : %s\n' % (self.removeURL))
        logSupport.dprint('CREDENTIALS    : %s\n' % creds)

        # Get curl & resposne object to use
        curl, response = curl_secure_context(self.removeURL)
        curl.setopt(curl.CUSTOMREQUEST, 'DELETE')

        try:
            curl.perform()
        except pycurl.error, error:
            errno, errstr = error
            print "PyCurl Error %s: %s" % (errno, errstr)
            logSupport.dprint(traceback.format_exc())
            raise JobSubClientError

        response_code = curl.getinfo(pycurl.RESPONSE_CODE)
        response_content_type = curl.getinfo(pycurl.CONTENT_TYPE)
        curl.close()

        print "Server response code: %s" % response_code
        if response_code == 200:
            value = response.getvalue()
            if response_content_type == 'application/json':
                response_dict = json.loads(value)
                response_err = response_dict.get('err')
                response_out = response_dict.get('out')
                print_formatted_response(response_out)
                print_formatted_response(response_err, msg_type='ERROR')
            else:
                print_formatted_response(value)
        response.close()


    def submit(self):
        post_data = [
            ('jobsub_args_base64', self.serverArgs_b64en)
        ]
        creds = get_client_credentials()

        logSupport.dprint('URL            : %s %s\n' % (self.submitURL, self.serverArgs_b64en))
        logSupport.dprint('CREDENTIALS    : %s\n' % creds)
        logSupport.dprint('SUBMIT_URL     : %s\n' % self.submitURL)
        logSupport.dprint('SERVER_ARGS_B64: %s\n' % base64.urlsafe_b64decode(self.serverArgs_b64en))
        #cmd = 'curl -k -X POST -d jobsub_args_base64=%s %s' % (self.serverArgs_b64en, self.submitURL)

        # Get curl & resposne object to use
        curl, response = curl_secure_context(self.submitURL)

        # Set additional curl options for submit
        curl.setopt(curl.POST, True)

        # If it is a local file upload the file
        if self.requiresFileUpload(self.jobExeURI):
            post_data.append(('jobsub_command', (pycurl.FORM_FILE, self.jobExe)))
        #curl.setopt(curl.POSTFIELDS, urllib.urlencode(post_fields))
        curl.setopt(curl.HTTPPOST, post_data)
        try:
            curl.perform()
        except pycurl.error, error:
            errno, errstr = error
            print "PyCurl Error %s: %s" % (errno, errstr)
            logSupport.dprint(traceback.format_exc())
            raise JobSubClientSubmissionError

        response_code = curl.getinfo(pycurl.RESPONSE_CODE)
        response_content_type = curl.getinfo(pycurl.CONTENT_TYPE)
        curl.close()

        print "Server response code: %s" % response_code
        if response_code == 200:
            value = response.getvalue()
            if response_content_type == 'application/json':
                response_dict = json.loads(value)
                response_err = response_dict.get('err')
                response_out = response_dict.get('out')
                print_formatted_response(response_out)
                print_formatted_response(response_err, msg_type='ERROR')
            else:
                print_formatted_response(value)
        response.close()


    def requiresFileUpload(self, uri):
        if uri:
            protocol = '%s://' % (uri.split('://'))[0]
            if protocol in constants.JOB_EXE_SUPPORTED_URIs:
                return True
        return False


    def help(self):
        curl, response = curl_secure_context(self.helpURL)
        return_value = None

        try:
            curl.perform()
        except pycurl.error, error:
            errno, errstr = error
            print "PyCurl Error %s: %s" % (errno, errstr)
            logSupport.dprint(traceback.format_exc())
            raise JobSubClientError

        response_code = curl.getinfo(pycurl.RESPONSE_CODE)
        response_content_type = curl.getinfo(pycurl.CONTENT_TYPE)
        curl.close()

        if response_code == 200:
            value = response.getvalue()
            if response_content_type == 'application/json':
                return_value = json.loads(value)
            else:
                return_value = value
        response.close()
        return return_value


def curl_secure_context(url):
    """
    Create a standard curl object for talking to http/https url set with most
    standard options used. Does not set client credentials.

    Returns the curl along with the response object
    """

    curl, response = curl_context(url)
    creds = get_client_credentials()

    curl.setopt(curl.SSLCERT, creds.get('cert'))
    curl.setopt(curl.SSLKEY, creds.get('key'))
    if platform.system() == 'Darwin':
        curl.setopt(curl.CAINFO, './ca-bundle.crt')
    else:
        curl.setopt(curl.CAPATH, get_capath())

    return (curl, response)


def curl_context(url):
    """
    Create a standard curl object for talking to https url set with most
    standard options used

    Returns the curl along with the response object
    """

    # Reponse from executing curl
    response = cStringIO.StringIO()

    # Create curl object and set curl options to use
    curl = pycurl.Curl()
    curl.setopt(curl.URL, url)
    #curl.setopt(curl.SSL_VERIFYHOST, constants.JOBSUB_SSL_VERIFYHOST)
    curl.setopt(curl.FAILONERROR, True)
    curl.setopt(curl.TIMEOUT, constants.JOBSUB_PYCURL_TIMEOUT)
    curl.setopt(curl.CONNECTTIMEOUT, constants.JOBSUB_PYCURL_CONNECTTIMEOUT)
    curl.setopt(curl.FAILONERROR, True)
    curl.setopt(curl.WRITEFUNCTION, response.write)
    curl.setopt(curl.HTTPHEADER, ['Accept: application/json'])

    return (curl, response)


def print_formatted_response(msg, msg_type='OUTPUT', ignore_empty_msg=True):
    if ignore_empty_msg and not msg:
        return
    print 'Response %s:' % msg_type
    if isinstance(msg, (str, int, float, unicode)):
        print '%s' % msg
    elif isinstance(msg, (list, tuple)):
        print '%s' % '\n'.join(msg)


def get_client_credentials():
    """
    Client credentials lookup follows following order until it finds them

    Do not look for user certificate and key in ~/.globus directory. It
    typically contains encrypted key and we could not get the server
    communication to work with it.

    1. $X509_USER_PROXY
    2. $X509_USER_CERT & $X509_USER_KEY
    3. Default proxy location: /tmp/x509up_u<UID>
    4. Kerberos ticket in $KRB5CCNAME. Convert it to proxy.
    5. Report failure
    """

    creds = {}
    cert = None
    key = None

    if os.environ.get('X509_USER_PROXY'):
        cert = os.environ.get('X509_USER_PROXY')
        key = os.environ.get('X509_USER_PROXY')
    elif (os.environ.get('X509_USER_CERT') and os.environ.get('X509_USER_KEY')):
        cert = os.environ.get('X509_USER_CERT')
        key = os.environ.get('X509_USER_KEY')
    elif os.path.exists(constants.X509_PROXY_DEFAULT_FILE):
        cert = key = constants.X509_PROXY_DEFAULT_FILE
    else:
        krb5_creds = jobsubClientCredentials.Krb5Ticket()
        if krb5_creds.isValid():
            jobsubClientCredentials.krb5cc_to_x509(krb5_creds.krb5CredCache)
            cert = key = constants.X509_PROXY_DEFAULT_FILE
        else:
            raise Exception("Cannot find credentials to use. Run 'kinit' to get a valid kerberos ticket or set X509 credentials related variables")

    return {'cert': cert, 'key': key}

def get_capath():
    system_ca_dir = '/etc/grid-security/certificates'
    ca_dir = None
    ca_dir = os.environ.get('X509_CERT_DIR')

    if (not ca_dir) and (os.path.exists(system_ca_dir)):
        ca_dir = system_ca_dir
    if not ca_dir:
        raise('Could not find CA Certificates. Set X509_CA_DIR')

    logSupport.dprint('Using CA_DIR: %s' % ca_dir)
    return ca_dir


###################################################################################
# INTERNAL - DO NOT USE OUTSIDE THIS CLASS
###################################################################################


def is_uri_supported(uri):
    protocol = '%s://' % (uri.split('://'))[0]
    if protocol in constants.JOB_EXE_SUPPORTED_URIs:
        return True
    return False


def get_server_env_exports(argv):
    # Any option -e should be extracted from the client and exported to the
    # server appropriately.
    env_vars = []
    exports = ''
    i = 0
    while(i < len(argv)):
        if argv[i] in constants.JOBSUB_SERVER_OPT_ENV:
            i += 1
            env_vars.append(argv[i])
        i += 1

    for var in env_vars:
        val = os.environ.get(var)
        if val:
            exports = 'export %s=%s;%s' % (var, val, exports)

    return exports


def get_jobexe_idx(argv):
    # Starting from the first arg parse the strings till you get one of the
    # supported URIs that indicate the job exe.
    # Skip the URI that follows certain options like -f which indicates input
    # files to upload

    i = 0
    exe_idx = None

    while(i < len(argv)):
        if argv[i] in constants.JOBSUB_SERVER_OPTS_WITH_URI:
            i += 1
        else:
            if is_uri_supported(argv[i]):
                return i
        i += 1

    return None


def get_jobexe_uri(argv):
    exe_idx = get_jobexe_idx(argv)
    job_exe = ''
    if exe_idx is not None:
        job_exe = argv[exe_idx]
    return job_exe


def uri2path(uri):
    return re.sub('^[a-z]+://', '', uri)


def get_dropbox_uri_map(argv):
    # make a map with keys of file path and value of sequence
    map = dict()
    idx = 0
    for arg in argv:
        if arg.startswith(constants.DROPBOX_SUPPORTED_URI):
            map[arg] = 'file%d' % idx
            idx += 1
    return map
