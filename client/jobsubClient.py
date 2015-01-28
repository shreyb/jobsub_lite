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
import cStringIO
import platform
import json
import copy
import traceback
import pprint 
import constants
import jobsubClientCredentials
import logSupport
import hashlib
import tempfile
import tarfile
import socket
import time


def version_string():
    ver = constants.__rpmversion__
    rel = constants.__rpmrelease__

    ver_str = ver

    # Release candidates are in rpmrelease with specific pattern
    p = re.compile('\.rc[1-9]+$')
    if rel:
        rc = p.findall(rel)
        if rc:
            ver_str = '%s-%s' % (ver, rc[-1].replace('.', ''))

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
                 dropboxServer=None, useDag=False, server_version='current'):
        self.server = server
        actual_server = server
        self.dropboxServer = dropboxServer
        self.serverVersion = server_version
        self.acctGroup = acct_group
        self.serverArgv = server_argv
        self.useDag=useDag
        self.serverPort = constants.JOBSUB_SERVER_DEFAULT_PORT
        serverParts=re.split(':',self.server)
        if len(serverParts) !=3:
            if len(serverParts)==1:
                self.server="https://%s:%s"%(serverParts[0],self.serverPort)
            if len(serverParts)==2:
                if serverParts[0].find('http')>=0:
                    self.server="%s:%s:%s"%(serverParts[0],serverParts[1],self.serverPort)
                else:
                    self.server="https://%s:%s"%(serverParts[0],serverParts[1])
        else:
            if serverParts[2]!=self.serverPort:
                self.serverPort=serverParts[2]
        self.credentials = get_client_credentials()
        self.acctRole = get_acct_role(acct_role, self.credentials.get('env_cert', self.credentials.get('cert')))

        # Help URL
        self.helpURL = constants.JOBSUB_ACCTGROUP_HELP_URL_PATTERN % (
                             self.server, self.acctGroup
                       )

        self.dagHelpURL = constants.JOBSUB_DAG_HELP_URL_PATTERN % (
                             self.server, self.acctGroup
                       )
        # TODO: Following is specific to the job submission and dropbox
        #       This should be pulled out of the constructor

        if self.serverArgv:
            self.jobExeURI = get_jobexe_uri(self.serverArgv)
            self.jobExe = uri2path(self.jobExeURI)
            d_idx=get_dropbox_idx(self.serverArgv)
            if d_idx is not None and d_idx<len(self.serverArgv):
                self.serverArgv=self.serverArgv[:d_idx]+self.serverArgv[d_idx].split('=')+self.serverArgv[d_idx+1:]
            self.jobDropboxURIMap = get_dropbox_uri_map(self.serverArgv)
            self.serverEnvExports = get_server_env_exports(self.serverArgv)
            srv_argv = copy.copy(self.serverArgv)
            if not os.path.exists(self.jobExe):
                err="You must supply a job executable. File '%s' not found. Exiting" % self.jobExe
                exeInTarball=False
                try:
                    dropbox_uri=get_dropbox_uri(self.serverArgv)
                    #print "dropbox_uri is %s"%dropbox_uri
                    tarball=uri2path(dropbox_uri)
                    contents=tarfile.open(tarball,'r').getnames()
                    if self.jobExe in contents or os.path.basename(self.jobExe) in contents:
                        exeInTarball=True
                    else:
                        for arg in self.serverArgv:
                            if arg in contents or os.path.basename(arg) in contents:
                                exeInTarball=True    
                                break
                    if exeInTarball:
                        pass
                    else:
                        raise JobSubClientError(err)

                except:
                
                    raise JobSubClientError(err)


            if self.jobDropboxURIMap:
                tfiles=[]
                # upload the files
                result = self.dropbox_upload()
                # replace uri with path on server
                for idx in range(0, len(srv_argv)):
                    arg = srv_argv[idx]
                    if arg.find(constants.DROPBOX_SUPPORTED_URI)>=0:
                        key = self.jobDropboxURIMap.get(arg)
                        if key is not None:
                            values = result.get(key)
                            if values is not None:
                                if self.dropboxServer is None:
                                    srv_argv[idx] = values.get('path')
                                    actual_server = "https://%s:8443/"%str(values.get('host'))
                                else:
                                    url = values.get('url')
                                    srv_argv[idx] = '%s%s' % (self.dropboxServer, url)
                                if srv_argv[idx] not in tfiles:
                                    tfiles.append(srv_argv[idx])
                            else:
                                print "Dropbox upload failed with error:"
                                print json.dumps(result)
                                raise JobSubClientSubmissionError
                if len(tfiles)>0:
                    transfer_input_files=','.join(tfiles)
                    self.serverEnvExports="export TRANSFER_INPUT_FILES=%s;%s"%(transfer_input_files,self.serverEnvExports)
                    if self.dropboxServer is None and self.server != actual_server:
                        self.server=actual_server

            if self.jobExeURI and self.jobExe:
                idx = get_jobexe_idx(srv_argv)
                if self.requiresFileUpload(self.jobExeURI):
                    srv_argv[idx] = '@%s' % self.jobExe

            if self.serverEnvExports:
                srv_env_export_b64en = base64.urlsafe_b64encode(self.serverEnvExports)
                srv_argv.insert(0, '--export_env=%s' % srv_env_export_b64en)

            self.serverArgs_b64en = base64.urlsafe_b64encode(' '.join(srv_argv))
        # Submit URL: Depends on the VOMS Role
        if self.acctRole:
            if self.useDag:
                self.submitURL = constants.JOBSUB_DAG_SUBMIT_URL_PATTERN_WITH_ROLE % (self.server, self.acctGroup, self.acctRole)
            else:
                self.submitURL = constants.JOBSUB_JOB_SUBMIT_URL_PATTERN_WITH_ROLE % (self.server, self.acctGroup, self.acctRole)
        elif self.useDag:
            self.submitURL = constants.JOBSUB_DAG_SUBMIT_URL_PATTERN % (self.server, self.acctGroup)
        else:
            self.submitURL = constants.JOBSUB_JOB_SUBMIT_URL_PATTERN % (self.server, self.acctGroup)


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
        response_time = 0
        try:
            stime = time.time()
            curl.perform()
            etime = time.time()
            response_time = etime - stime
        except pycurl.error, error:
            errno, errstr = error
            err= "PyCurl Error %s: %s" % (errno, errstr)
            logSupport.dprint(traceback.format_exc())
            raise JobSubClientSubmissionError(err)

        response_code = curl.getinfo(pycurl.RESPONSE_CODE)
        response_content_type = curl.getinfo(pycurl.CONTENT_TYPE)
        serving_server = servicing_jobsub_server(curl)
        curl.close()

        print "SERVER RESPONSE CODE: %s" % response_code
        if response_code == 200:
            value = response.getvalue()
            if response_content_type == 'application/json':
                result = json.loads(value)
            else:
                print_formatted_response(value, response_code, self.server,
                                         serving_server, response_time)
        response.close()

        return result


    def submit_dag(self):
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
        # If we uploaded a dropbox file we saved the actual hostname to
        # self.server and self.submitURL so disable SSL_VERIFYHOST
        if self.jobDropboxURIMap and self.dropboxServer is None:
            curl.setopt(curl.SSL_VERIFYHOST, 0)

        # If it is a local file upload the file
        if self.requiresFileUpload(self.jobExeURI):
            post_data.append(('jobsub_command', (pycurl.FORM_FILE, self.jobExe)))
            payloadFileName=self.makeDagPayload(uri2path(self.jobExeURI))
            post_data.append(('jobsub_payload', (pycurl.FORM_FILE, payloadFileName)))
        #curl.setopt(curl.POSTFIELDS, urllib.urlencode(post_fields))
        curl.setopt(curl.HTTPPOST, post_data)
        http_code = 200
        response_time = 0
        try:
            stime = time.time()
            curl.perform()
            etime = time.time()
            response_time = etime - stime
            http_code = curl.getinfo(pycurl.RESPONSE_CODE)
        except pycurl.error, error:
            errno, errstr = error
            http_code = curl.getinfo(pycurl.RESPONSE_CODE)
            err = "HTTP response:%s PyCurl Error %s: %s" % (http_code, errno,
                                                            errstr)
            logSupport.dprint(traceback.format_exc())
            if errno == 60:
                err += "\nDid you remember to include the port number to "
                err += "your server specification \n( --jobsub-server %s )?"%self.server 
            logSupport.dprint(traceback.format_exc())
            raise JobSubClientSubmissionError(err)

        self.printResponse(curl, response, response_time)
        curl.close()
        response.close()
        return http_code


    def makeDagPayload(self,infile):
        orig=os.getcwd()
        dirpath=tempfile.mkdtemp()
        fin=open(infile,'r')
        z=fin.read()
        os.chdir(dirpath)
        fnameout="%s"%(os.path.basename(infile))
        fout=open(fnameout,'w')
        tar = tarfile.open('payload.tgz','w:gz')
        
        lines=z.split('\n')
        for l in lines:
            wrds=re.split('\s+',l)
            la=[]
            for w in wrds:
                w2=uri2path(w)
                if w != w2 :
                    b=os.path.basename(w2)
                    w3=" ${JOBSUB_EXPORTS} ./%s"%b
                    la.append(w3)
                    os.chdir(orig)
                    tar.add(uri2path(w),b)
                    os.chdir(dirpath)
                else:
                    la.append(w)
            la.append('\n')
            l2=' '.join(la)
            fout.write(l2)
    
    
        fin.close()
        fout.close()
        tar.add(fnameout,fnameout)
        tar.close()
        return "%s/payload.tgz" % dirpath


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
        # If we uploaded a dropbox file we saved the actual hostname to
        # self.server and self.submitURL so disable SSL_VERIFYHOST
        if self.jobDropboxURIMap and self.dropboxServer is None:
            curl.setopt(curl.SSL_VERIFYHOST, 0)

        # If it is a local file upload the file
        if self.requiresFileUpload(self.jobExeURI):
            post_data.append(('jobsub_command', (pycurl.FORM_FILE, self.jobExe)))
        #curl.setopt(curl.POSTFIELDS, urllib.urlencode(post_fields))
        curl.setopt(curl.HTTPPOST, post_data)

        http_code = 200
        response_time = 0
        try:
            stime = time.time()
            curl.perform()
            etime = time.time()
            response_time = etime - stime
            http_code = curl.getinfo(pycurl.RESPONSE_CODE)
        except pycurl.error, error:
            errno, errstr = error
            http_code = curl.getinfo(pycurl.RESPONSE_CODE)
            err="HTTP response:%s PyCurl Error %s: %s" % (http_code, errno,
                                                          errstr)
            if errno == 60:
                err += "\nDid you remember to include the port number to "
                err += "your server specification \n( --jobsub-server %s )?"%self.server
            logSupport.dprint(traceback.format_exc())
            raise JobSubClientSubmissionError(err)

        self.printResponse(curl, response, response_time)
        curl.close()
        response.close()
        return http_code


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

        http_code = 200
        response_time = 0
        try:
            stime = time.time()
            curl.perform()
            etime = time.time()
            response_time = etime - stime
            http_code = curl.getinfo(pycurl.RESPONSE_CODE)
        except pycurl.error, error:
            errno, errstr = error
            http_code = curl.getinfo(pycurl.RESPONSE_CODE)
            err = "HTTP response:%s PyCurl Error %s: %s" % (http_code,errno, errstr)
            if errno == 60:
                err=err+"\nDid you remember to include the port number to "
                err=err+"your server specification \n( --jobsub-server %s )?"%self.server
            logSupport.dprint(traceback.format_exc())
            raise JobSubClientError(err)

        self.printResponse(curl, response, response_time)
        curl.close()
        response.close()
        return http_code


    def checkID(self,jobid):
        if jobid is None:
            return jobid
        if jobid.find('@')>=0:
            jobidparts = jobid.split('@')
            server=jobidparts[-1]
            jobid='@'.join(jobidparts[:-1])
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

        return self.changeJobState(self.releaseURL, 'PUT', post_data)


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

        return self.changeJobState(self.holdURL, 'PUT', post_data)


    def remove(self, jobid):
        #jobid=self.checkID(jobid)
        if self.acctRole:
            self.removeURL = constants.JOBSUB_JOB_REMOVE_URL_PATTERN_WITH_ROLE % (self.server, self.acctGroup, self.acctRole, jobid)
        else:
            self.removeURL = constants.JOBSUB_JOB_REMOVE_URL_PATTERN % (
                                 self.server, self.acctGroup, jobid
                             )

        return self.changeJobState(self.removeURL, 'DELETE')


    def history(self, userid=None, jobid=None,outFormat=None):
        servers = get_jobsub_server_aliases(self.server)
        jobid = self.checkID(jobid)

        rc = 0
        for server in servers:
            if jobid is None and userid is None:
                self.histURL = constants.JOBSUB_HISTORY_URL_PATTERN % (
                                   server, self.acctGroup)
            else:
                self.histURL = constants.JOBSUB_HISTORY_WITH_USER_PATTERN % (
                                   server, self.acctGroup, userid)
            if jobid is not None:
                self.histURL = "%s?job_id=%s"%(self.histURL,jobid)

            if outFormat is not None:
                self.histURL="%s%s/"%(self.histURL,outFormat)
            try:
                http_code = self.changeJobState(self.histURL, 'GET',
                                                ssl_verifyhost=False)
                rc += http_code_to_rc(http_code)
            except:
                print 'Error retrieving history from the server %s' % server
                rc += 1
                logSupport.dprint(traceback.format_exc())
        return rc


    def summary(self):
        self.listURL = constants.JOBSUB_Q_SUMMARY_URL_PATTERN % (self.server)
        return self.changeJobState(self.listURL, 'GET')

    def listConfiguredSites(self):
        self.listURL=constants.JOBSUB_CONFIGURED_SITES_URL_PATTERN%(self.server,self.acctGroup)
        return self.changeJobState(self.listURL,'GET')

    def listJobs(self, jobid=None, userid=None,outFormat=None):
        #jobid=self.checkID(jobid)
        if jobid is None and self.acctGroup is None and userid is None:
            self.listURL = constants.JOBSUB_Q_NO_GROUP_URL_PATTERN % self.server
        elif userid is not None:
            tmpURL = constants.JOBSUB_Q_USERID_URL_PATTERN % ( self.server, userid)
            if self.acctGroup is not None:
                tmpURL="%sacctgroup/%s/"%(tmpURL,self.acctGroup)
            if jobid is not None:
                tmpURL="%s%s/"%(tmpURL,jobid)
            self.listURL = tmpURL
        elif self.acctGroup is not None:
            tmpURL = constants.JOBSUB_Q_WITH_GROUP_URL_PATTERN % (self.server, self.acctGroup)
            if jobid is not None:
                tmpURL="%s%s/"% ( tmpURL, jobid)
            self.listURL = tmpURL
        else :
            self.listURL = constants.JOBSUB_Q_JOBID_URL_PATTERN % ( self.server, jobid)

        if outFormat is not None:
            self.listURL="%s%s/"%(self.listURL,outFormat)
        return self.changeJobState(self.listURL, 'GET')


    def requiresFileUpload(self, uri):
        if uri:
            protocol = '%s://' % (uri.split('://'))[0]
            if protocol in constants.JOB_EXE_SUPPORTED_URIs:
                return os.path.exists(uri2path(uri))
        return False


    def help(self,helpType='jobsubHelp'):

        helpURL=self.helpURL
        if helpType=='dag':
            helpURL=self.dagHelpURL

        curl, response = curl_secure_context(helpURL, self.credentials)
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


    def extractResponseDetails(self, curl, response):
        content_type = curl.getinfo(pycurl.CONTENT_TYPE)
        code = curl.getinfo(pycurl.RESPONSE_CODE)
        value = response.getvalue()
        serving_server = servicing_jobsub_server(curl)
        return (content_type, code, value, serving_server)



    def printResponse(self, curl, response, response_time):
        """
        Given the curl and response objects print the response on screen
        """

        content_type, code, value, serving_server = self.extractResponseDetails(
                                                        curl, response)

        if content_type == 'application/json':
            print_json_response(value, code, self.server,
                                serving_server, response_time)
        else:
            print_formatted_response(value, code, self.server,
                                     serving_server, response_time)


def get_jobsub_server_aliases(server):
    # Set of hosts in the HA mode
    aliases = set()

    host_port = server.replace('https://', '')
    host_port = host_port.replace('/', '')
    tokens = host_port.split(':')
    if tokens and (len(tokens) <= 2):
        host = tokens[0] 
        if len(tokens) == 2:
            port = tokens[1] 
        else:
            port = constants.JOBSUB_SERVER_DEFAULT_PORT
        # Filter bu TCP ports (5th arg = 6 below)
        addr_info = socket.getaddrinfo(host, port, 0, 0, 6)
        for info in addr_info:
            # Each info is of the form (2, 1, 6, '', ('131.225.67.139', 8443))
            ip, p = info[4]
            js_s = constants.JOBSUB_SERVER_URL_PATTERN % (socket.gethostbyaddr(ip)[0], p)
            aliases.add(js_s)

    if not aliases:
        # Just return the default one
        aliases.add(server)

    return aliases
    

def servicing_jobsub_server(curl):
    server = 'UNKNOWN'
    try:
        ip = curl.getinfo(pycurl.PRIMARY_IP)
        server = constants.JOBSUB_SERVER_URL_PATTERN % (
                     socket.gethostbyaddr(ip)[0],
                     constants.JOBSUB_SERVER_DEFAULT_PORT)
    except:
        # Ignore errors. This is not critical
        pass
    return server

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
    curl.setopt(curl.URL, str(url))
    curl.setopt(curl.FAILONERROR, False)
    curl.setopt(curl.TIMEOUT, constants.JOBSUB_PYCURL_TIMEOUT)
    curl.setopt(curl.CONNECTTIMEOUT, constants.JOBSUB_PYCURL_CONNECTTIMEOUT)
    curl.setopt(curl.WRITEFUNCTION, response.write)
    curl.setopt(curl.HTTPHEADER, ['Accept: application/json'])

    return (curl, response)


def print_msg(msg):
    if isinstance(msg, (str, int, float, unicode)):
        print '%s' % (msg)
    elif isinstance(msg, (list, tuple)):
        print '%s' % '\n'.join(msg)
    elif isinstance(msg, (dict)):
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(msg)
  

def print_server_details(response_code, server, serving_server, response_time):
    print >> sys.stderr, ''
    print >> sys.stderr, 'JOBSUB SERVER CONTACTED     : %s' % server
    print >> sys.stderr, 'JOBSUB SERVER RESPONDED     : %s' % serving_server
    print >> sys.stderr, 'JOBSUB SERVER RESPONSE CODE : %s (%s)' % (
                             response_code,
                             constants.HTTP_RESPONSE_CODE_STATUS.get(
                                 response_code,
                                 'Failed'))
    print >> sys.stderr, 'JOBSUB SERVER SERVICED IN   : %s sec' % response_time
    print >> sys.stderr, 'JOBSUB CLIENT FQDN          : %s' % socket.gethostname()
    print >> sys.stderr, 'JOBSUB CLIENT SERVICED TIME : %s' % time.strftime('%d/%b/%Y %X')


def print_json_response(response, response_code, server, serving_server,
                        response_time, ignore_empty_msg=True):
    response_dict = json.loads(response)
    output = response_dict.get('out')
    error = response_dict.get('err')
    # Print output and error
    if output:
        print_msg(output)
    if error or not ignore_empty_msg:
        print 'RESPONSE ERROR:'
        print_msg(error)
    print_server_details(response_code, server, serving_server, response_time)

   

def print_formatted_response(msg, response_code, server, serving_server,
                             response_time, msg_type='OUTPUT',
                             ignore_empty_msg=True, print_msg_type=True):
    if ignore_empty_msg and not msg:
        return
    if print_msg_type:
        print 'Response %s:' % msg_type
    print_msg(msg)
    print_server_details(response_code, server, serving_server, response_time)


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

    env_cert = None
    env_key = None
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
        raise JobSubClientError('Could not find CA Certificates in %s. Set X509_CERT_DIR in the environment.' % system_ca_dir)
    logSupport.dprint('Using CA_DIR: %s' % ca_dir)
    return ca_dir


################################################################################
# INTERNAL - DO NOT USE OUTSIDE THIS CLASS
################################################################################

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
    # also --environment and --environment=
    # server appropriately.
    env_vars = []
    exports = ''
    i = 0
    while(i < len(argv)):
        idx=argv[i].find('=')
        if idx>=0:
            arg=argv[i][:idx]
            val=argv[i][idx+1:]
        else:
            arg=argv[i]
            val=None
        
        if arg in constants.JOBSUB_SERVER_OPT_ENV:
            if val is None: 
                i += 1
                val=argv[i]
            env_vars.append(val)
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

    while(i < len(argv)):
        if argv[i] in constants.JOBSUB_SERVER_OPTS_WITH_URI:
            i += 1
        else:
            if is_uri_supported(argv[i]):
                return i
        i += 1

    return None

def get_dropbox_idx(argv):

    i = 0
    while(i < len(argv)):
        if argv[i].find(constants.DROPBOX_SUPPORTED_URI)<0: 
            i += 1
        else:
            return i

    return None

def get_dropbox_uri(argv):
    dropbox_idx = get_dropbox_idx(argv)
    dropbox_uri = None
    if dropbox_idx is not None:
        dropbox_uri = argv[dropbox_idx]
        if dropbox_uri.find('=')>0:
            parts=dropbox_uri.split('=')
            for part in parts:
                if part.find(constants.DROPBOX_SUPPORTED_URI)>=0:
                    dropbox_uri=part.strip()
                    return dropbox_uri
    return dropbox_uri

def get_jobexe_uri(argv):
    exe_idx = get_jobexe_idx(argv)
    job_exe = ''
    if exe_idx is not None:
        job_exe = argv[exe_idx]
    return job_exe


def uri2path(uri):
    return re.sub('^.\S+://', '', uri)


def get_dropbox_uri_map(argv):
    # make a map with keys of file path and value of sequence
    map = dict()
    for arg in argv:
        if arg.find(constants.DROPBOX_SUPPORTED_URI)>=0:
            map[arg] = digest_for_file(uri2path(arg))
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


def http_code_to_rc(http_code):
    if http_code >= 200 and http_code < 300:
        return 0
    return 1
