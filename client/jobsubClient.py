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
import pprint 
import constants
import jobsubClientCredentials
import logSupport
from distutils import spawn
import subprocess 
import hashlib

def version_string():
    ver = constants.__rpmversion__
    rel = constants.__rpmrelease__

    ver_str = ver

    # Release candidates are in rpmrelease with specific pattern
    p = re.compile('\.rc[1-9]+$')
    if rel:
        rc = p.findall(rel)
        if rc:
            ver_str = '%s %s' % (ver, rc[-1].replace('.', ''))

    return ver_str


class JobSubClientError(Exception):
    def __init__(self,errMsg="JobSub client action failed."):
        sys.exit(errMsg)
        Exception.__init__(self, errMsg)


class JobSubClientSubmissionError(Exception):
    def __init__(self,errMsg="JobSub remote submission failed."):
        sys.exit(errMsg)
        Exception.__init__(self, errMsg)


class JobSubClient:

    def __init__(self, server, acct_group, acct_role, server_argv,
                 dropboxServer=None, server_version='current'):
        self.server = server
        self.dropboxServer = dropboxServer
        self.serverVersion = server_version
        self.acctGroup = acct_group
        self.serverArgv = server_argv

        self.credentials = get_client_credentials()
        self.acctRole = get_acct_role(acct_role, self.credentials.get('env_cert', self.credentials.get('cert')))

        # Help URL
        self.helpURL = constants.JOBSUB_ACCTGROUP_HELP_URL_PATTERN % (
                             self.server, self.acctGroup
                       )
        # Submit URL: Depends on the VOMS Role
        if self.acctRole:
            self.submitURL = constants.JOBSUB_JOB_SUBMIT_URL_PATTERN_WITH_ROLE % (self.server, self.acctGroup, self.acctRole)
        else:
            self.submitURL = constants.JOBSUB_JOB_SUBMIT_URL_PATTERN % (self.server, self.acctGroup)

        # TODO: Following is specific to the job submission and dropbox
        #       This should be pulled out of the constructor

        if self.serverArgv:
            self.jobExeURI = get_jobexe_uri(self.serverArgv)
            self.jobExe = uri2path(self.jobExeURI)
            self.jobDropboxURIMap = get_dropbox_uri_map(self.serverArgv)
            self.serverEnvExports = get_server_env_exports(server_argv)
            srv_argv = copy.copy(server_argv)
            if not os.path.exists(self.jobExe):
                err="You must supply a job executable. File '%s' not found. Exiting" % self.jobExe
                raise JobSubClientError(err)
                
            if self.jobDropboxURIMap:
		tfiles=[]
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
				tfiles.append(srv_argv[idx])
                            else:
                                print "Dropbox upload failed with error:"
                                print json.dumps(result)
                                raise JobSubClientSubmissionError
		if len(tfiles)>0:
			transfer_input_files=','.join(tfiles)
			self.serverEnvExports="export TRANSFER_INPUT_FILES=%s;%s"%(transfer_input_files,self.serverEnvExports)

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
        post_data = list()

        dropboxURL = constants.JOBSUB_DROPBOX_POST_URL_PATTERN % (self.dropboxServer or self.server, self.acctGroup)

        # Create curl object and set curl options to use
        curl, response = curl_secure_context(dropboxURL, self.credentials)
        curl.setopt(curl.POST, True)

        # If it is a local file upload the file
        for file, key in self.jobDropboxURIMap.items():
            post_data.append((key, (pycurl.FORM_FILE, uri2path(file))))
        curl.setopt(curl.HTTPPOST, post_data)
        try:
            curl.perform()
        except pycurl.error, error:
            errno, errstr = error
            err= "PyCurl Error %s: %s" % (errno, errstr)
            logSupport.dprint(traceback.format_exc())
            raise JobSubClientSubmissionError(err)

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


    def submit(self):
        post_data = [
            ('jobsub_args_base64', self.serverArgs_b64en),
            ('jobsub_client_version', version_string()),
        ]

        logSupport.dprint('URL            : %s %s\n' % (self.submitURL, self.serverArgs_b64en))
        logSupport.dprint('CREDENTIALS    : %s\n' % self.credentials)
        logSupport.dprint('SUBMIT_URL     : %s\n' % self.submitURL)
        logSupport.dprint('SERVER_ARGS_B64: %s\n' % base64.urlsafe_b64decode(self.serverArgs_b64en))
        #cmd = 'curl -k -X POST -d jobsub_args_base64=%s %s' % (self.serverArgs_b64en, self.submitURL)

        # Get curl & resposne object to use
        curl, response = curl_secure_context(self.submitURL, self.credentials)

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
            err="PyCurl Error %s: %s" % (errno, errstr)
            logSupport.dprint(traceback.format_exc())
            raise JobSubClientSubmissionError(err)

        self.printResponse(curl, response)
        curl.close()
        response.close()


    def changeJobState(self, url, http_custom_request, post_data=None,
                       ssl_verifyhost=True):
        """
        Generic API to perform job actions like remove/hold/release
        """

        logSupport.dprint('ACTION URL     : %s\n' % url)
        logSupport.dprint('CREDENTIALS    : %s\n' % self.credentials)

        # Get curl & resposne object to use
        curl, response = curl_secure_context(url, self.credentials)
        curl.setopt(curl.CUSTOMREQUEST, http_custom_request)
        if post_data:
            curl.setopt(curl.HTTPPOST, post_data)
        if not ssl_verifyhost:
            curl.setopt(curl.SSL_VERIFYHOST, 0)

        try:
            curl.perform()
        except pycurl.error, error:
            errno, errstr = error
            x=curl.getinfo(pycurl.RESPONSE_CODE)
            if True:
                err = "HTTP response:%s PyCurl Error %s: %s" % (x,errno, errstr)
                if errno == 60:
                    err=err+"\nDid you remember to include the port number to "
                    err=err+"your server specification \n( --jobsub-server %s )?"%self.server 
            	logSupport.dprint(traceback.format_exc())
            	raise JobSubClientError(err)

        self.printResponse(curl, response)
        curl.close()
        response.close()

    def checkID(self,jobid):
        if jobid is None:
            return jobid
        if jobid.find('@')>=0:
            jobid,server = jobid.split('@')
            self.server="https://%s:8443"%server
        if jobid=='':
            jobid = None
        return jobid

    def release(self, jobid):
        #jobid=self.checkID(jobid)
        post_data = [
            ('job_action', 'RELEASE')
        ]
        if self.acctRole:
            self.releaseURL = constants.JOBSUB_JOB_RELEASE_URL_PATTERN_WITH_ROLE % (self.server, self.acctGroup, self.acctRole, jobid)
        else:
            self.releaseURL = constants.JOBSUB_JOB_RELEASE_URL_PATTERN % (
                                 self.server, self.acctGroup, jobid
                             )

        self.changeJobState(self.releaseURL, 'PUT', post_data)


    def hold(self, jobid):
        #jobid=self.checkID(jobid)
        post_data = [
            ('job_action', 'HOLD')
        ]
        if self.acctRole:
            self.holdURL = constants.JOBSUB_JOB_HOLD_URL_PATTERN_WITH_ROLE % (self.server, self.acctGroup, self.acctRole, jobid)
        else:
            self.holdURL = constants.JOBSUB_JOB_HOLD_URL_PATTERN % (
                                 self.server, self.acctGroup, jobid
                             )

        self.changeJobState(self.holdURL, 'PUT', post_data)


    def remove(self, jobid):
        #jobid=self.checkID(jobid)
        if self.acctRole:
            self.removeURL = constants.JOBSUB_JOB_REMOVE_URL_PATTERN_WITH_ROLE % (self.server, self.acctGroup, self.acctRole, jobid)
        else:
            self.removeURL = constants.JOBSUB_JOB_REMOVE_URL_PATTERN % (
                                 self.server, self.acctGroup, jobid
                             )

        self.changeJobState(self.removeURL, 'DELETE')

    def history(self, userid=None, jobid=None):
            jobid=self.checkID(jobid)
            if jobid is None and userid is None:
                self.histURL = constants.JOBSUB_HISTORY_URL_PATTERN % (self.server, self.acctGroup)
            else:
                self.histURL = constants.JOBSUB_HISTORY_WITH_USER_PATTERN % (
                                 self.server, self.acctGroup, userid
                             )
            if jobid is not None:
                self.histURL = "%s?job_id=%s"%(self.histURL,jobid)

            self.changeJobState(self.histURL, 'GET', ssl_verifyhost=False)

    def summary(self):
            self.listURL = constants.JOBSUB_Q_SUMMARY_URL_PATTERN % ( self.server)
            self.changeJobState(self.listURL, 'GET')


    def list(self, jobid=None):
            #jobid=self.checkID(jobid)
            if jobid is None and self.acctGroup is None:
                self.listURL = constants.JOBSUB_Q_NO_GROUP_URL_PATTERN % self.server
            elif jobid is None:
                self.listURL = constants.JOBSUB_Q_WITH_GROUP_URL_PATTERN % (self.server, self.acctGroup)
            else:
                self.listURL = constants.JOBSUB_Q_GROUP_JOBID_URL_PATTERN % (
                                 self.server, self.acctGroup, jobid
                             )

            self.changeJobState(self.listURL, 'GET')

    def requiresFileUpload(self, uri):
        if uri:
            protocol = '%s://' % (uri.split('://'))[0]
            if protocol in constants.JOB_EXE_SUPPORTED_URIs:
                return True
        return False


    def help(self):
        curl, response = curl_secure_context(self.helpURL, self.credentials)
        return_value = None

        try:
            curl.perform()
        except pycurl.error, error:
            errno, errstr = error
            err="PyCurl Error %s: %s" % (errno, errstr)
            logSupport.dprint(err)
            logSupport.dprint(traceback.format_exc())
            raise JobSubClientError(err)

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


    def printResponse(self, curl, response):
        """
        Given the curl and response objects print the response on screen
        """

        response_code = curl.getinfo(pycurl.RESPONSE_CODE)
        response_content_type = curl.getinfo(pycurl.CONTENT_TYPE)
        print "Server response code: %s" % response_code
        value = response.getvalue()
        if response_content_type == 'application/json':
            try:
                response_dict = json.loads(value)
                response_err = response_dict.get('err')
                response_out = response_dict.get('out')
                print_formatted_response(response_out)
                print_formatted_response(response_err, msg_type='ERROR')
            except:
                print_formatted_response(value)
        else:
            print_formatted_response(value)


def curl_secure_context(url, credentials):
    """
    Create a standard curl object for talking to http/https url set with most
    standard options used. Does not set client credentials.

    Returns the curl along with the response object
    """

    curl, response = curl_context(url)

    curl.setopt(curl.SSLCERT, credentials.get('cert'))
    curl.setopt(curl.SSLKEY, credentials.get('key'))
    curl.setopt(curl.SSL_VERIFYHOST, constants.JOBSUB_SSL_VERIFYHOST)
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
    curl.setopt(curl.FAILONERROR, False)
    curl.setopt(curl.TIMEOUT, constants.JOBSUB_PYCURL_TIMEOUT)
    curl.setopt(curl.CONNECTTIMEOUT, constants.JOBSUB_PYCURL_CONNECTTIMEOUT)
    curl.setopt(curl.WRITEFUNCTION, response.write)
    curl.setopt(curl.HTTPHEADER, ['Accept: application/json'])

    return (curl, response)


def print_formatted_response(msg, msg_type='OUTPUT', ignore_empty_msg=True):
    if ignore_empty_msg and not msg:
        return
    print 'Response %s:' % msg_type
    if isinstance(msg, (str, int, float, unicode)):
        print '%s' % (msg)
    elif isinstance(msg, (list, tuple)):
        print '%s' % '\n'.join(msg)
    elif isinstance(msg, (dict)):
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(msg)


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
    env_cert = cert = None
    env_key = key = None
    cred_dict={}
    if os.environ.get('X509_USER_PROXY'):
        env_cert = os.environ.get('X509_USER_PROXY')
        env_key = os.environ.get('X509_USER_PROXY')
    elif (os.environ.get('X509_USER_CERT') and os.environ.get('X509_USER_KEY')):
        env_cert = os.environ.get('X509_USER_CERT')
        env_key = os.environ.get('X509_USER_KEY')
    elif os.path.exists(constants.X509_PROXY_DEFAULT_FILE):
        env_cert = env_key = constants.X509_PROXY_DEFAULT_FILE
    if env_cert is not None:
        cred_dict['env_cert']=env_cert
        cred_dict['env_key']=env_key
    krb5_creds = jobsubClientCredentials.Krb5Ticket()
    if krb5_creds.isValid():
        jobsubClientCredentials.krb5cc_to_x509(krb5_creds.krb5CredCache)
        cred_dict['cert']=cred_dict['key'] = constants.X509_PROXY_DEFAULT_FILE
    else:
        raise JobSubClientError("Cannot find credentials to use. Run 'kinit' to get a valid kerberos ticket or set X509 credentials related variables")

    return cred_dict

def get_capath():
    system_ca_dir = '/etc/grid-security/certificates'
    ca_dir = None
    ca_dir = os.environ.get('X509_CERT_DIR')

    if (not ca_dir) and (os.path.exists(system_ca_dir)):
        ca_dir = system_ca_dir
    if not ca_dir:
        raise JobSubClientError('Could not find CA Certificates. Set X509_CA_DIR')

    logSupport.dprint('Using CA_DIR: %s' % ca_dir)
    return ca_dir

          

###################################################################################
# INTERNAL - DO NOT USE OUTSIDE THIS CLASS
###################################################################################

def get_acct_role(acct_role, proxy):
    role = acct_role
    if not role:
        # If no role is specified, try to extract it from VOMS proxy
        voms_proxy = jobsubClientCredentials.VOMSProxy(proxy)
        if voms_proxy.fqan:
            match = re.search('/Role=(.*)/', voms_proxy.fqan[0]) 
            if match.group(1) != 'NULL':
                role = match.group(1)
    return role


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
            map[arg] = digest_for_file(uri2path(arg))
            idx += 1
    return map


def digest_for_file(fileName, block_size=2**20):
    dig = hashlib.sha1()
    f=open(fileName,'r')
    while True:
        data = f.read(block_size)
        if not data:
            break
        dig.update(data)
    f.close()
    x=dig.hexdigest()
    return x
