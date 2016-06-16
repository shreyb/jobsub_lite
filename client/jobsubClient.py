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
import shutil
import urllib
from datetime import datetime 
from signal import signal, SIGPIPE, SIG_DFL



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
                 dropboxServer=None, useDag=False, server_version='current', extra_opts={}):
        self.server = server
        self.initial_server = server
        actual_server = server
        self.dropboxServer = dropboxServer
        self.serverVersion = server_version
        self.acctGroup = acct_group
        self.serverArgv = server_argv
        self.useDag = useDag
        self.serverPort = constants.JOBSUB_SERVER_DEFAULT_PORT
        self.extra_opts = extra_opts
        self.verbose = extra_opts.get('debug',False)
        self.better_analyze = extra_opts.get('better_analyze',False)
        self.forcex = extra_opts.get('forcex',False)
        self.schedd_list = []
        serverParts=re.split(':',self.server)
        if len(serverParts) !=3:
            if len(serverParts)==1:
                self.server="https://%s:%s"%(serverParts[0],self.serverPort)
            if len(serverParts) == 2:
                if serverParts[0].find('http') >= 0:
                    self.server="%s:%s:%s"%(serverParts[0],serverParts[1],self.serverPort)
                else:
                    self.server = "https://%s:%s"%(serverParts[0], serverParts[1])
        else:
            if serverParts[2]!= self.serverPort:
                self.serverPort = serverParts[2]
        self.credentials = get_client_credentials(acctGroup=self.acctGroup, server=self.server)
        cert = self.credentials.get('env_cert', self.credentials.get('cert'))
        self.issuer = jobsubClientCredentials.proxy_issuer(cert)
        self.acctRole = get_acct_role(acct_role, cert)

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
                err="You must supply a job executable, preceded by the directive 'file://' which is used to find the executable in jobsub_submit's  command line.  File '%s' not found. Exiting" % self.jobExe
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


    def dropbox_upload(self):
        result = dict()
        post_data = list()
        orig_server = self.server
        self.probeSchedds()

        dropboxURL = constants.JOBSUB_DROPBOX_POST_URL_PATTERN % (self.dropboxServer or self.server, self.acctGroup)

        # Create curl object and set curl options to use
        curl, response = curl_secure_context(dropboxURL, self.credentials)
        curl.setopt(curl.POST, True)
        if self.server != orig_server:
            curl.setopt(curl.SSL_VERIFYHOST, 0)

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
                                         serving_server, response_time, verbose=self.verbose)
        response.close()

        return result


    def submit_dag(self):
        if (not self.jobDropboxURIMap) or self.dropboxServer:
            self.probeSchedds()
        self.serverAuthMethods()
        if self.acctRole:
            self.submitURL = constants.JOBSUB_DAG_SUBMIT_URL_PATTERN_WITH_ROLE % (self.server, self.acctGroup, self.acctRole)
        else:
            self.submitURL = constants.JOBSUB_DAG_SUBMIT_URL_PATTERN % (self.server, self.acctGroup)
        krb5_principal = jobsubClientCredentials.krb5_default_principal()
        post_data = [
            ('jobsub_args_base64', self.serverArgs_b64en),
            ('jobsub_client_version', version_string()),
            ('jobsub_client_krb5_principal', krb5_principal),
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
        #if we select the best schedd we have to disable this
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
        shutil.rmtree(os.path.dirname(payloadFileName), ignore_errors=True)

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
        if (not self.jobDropboxURIMap) or self.dropboxServer:
            self.probeSchedds()
        self.serverAuthMethods()
        
        if self.acctRole:
            self.submitURL = constants.JOBSUB_JOB_SUBMIT_URL_PATTERN_WITH_ROLE % (self.server, self.acctGroup, self.acctRole)
        else:
            self.submitURL = constants.JOBSUB_JOB_SUBMIT_URL_PATTERN % (self.server, self.acctGroup)
        krb5_principal = jobsubClientCredentials.krb5_default_principal()
        post_data = [
            ('jobsub_args_base64', self.serverArgs_b64en),
            ('jobsub_client_version', version_string()),
            ('jobsub_client_krb5_principal', krb5_principal),
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
        #always have to do this now as we select the best schedd and submit directly to it
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
        else:
            p=re.compile('^[0-9]+\.*[0-9]*\@[\w]+-*_*[\w]*.fnal.gov$')
            if not p.match(jobid):
                err = "ERROR: --jobid '%s' is malformed" % jobid
                raise JobSubClientError(err)
            return jobid


    def release(self, jobid=None, uid=None, constraint=None):
        jobid=self.checkID(jobid)
        post_data = [
            ('job_action', 'RELEASE')
        ]
        if constraint:
            self.probeSchedds()
            rslts = []
            for schedd in self.schedd_list:
                srv = "https://%s:8443"%schedd
                self.actionURL = constants.JOBSUB_JOB_CONSTRAINT_URL_PATTERN \
                        % ( srv, self.acctGroup, urllib.quote(constraint) )
                if uid:
                    self.actionURL = "%s%s/" % (self.actionURL, uid)
                rslts.append(self.changeJobState(self.actionURL, 'PUT', post_data, ssl_verifyhost=False))
            return rslts
        elif uid:
            self.probeSchedds()
            rslts = []
            item = uid
            for schedd in self.schedd_list:
                srv = "https://%s:8443"%schedd
                if self.acctRole:
                    self.actionURL = constants.JOBSUB_JOB_RELEASE_BYUSER_URL_PATTERN_WITH_ROLE\
                        % (srv, self.acctGroup, self.acctRole, item)
                else:
                    self.actionURL = constants.JOBSUB_JOB_RELEASE_BYUSER_URL_PATTERN\
                        % ( srv, self.acctGroup, item )
                if jobid:
                    self.actionURL = "%s%s/" % (self.actionURL, jobid)
                rslts.append(self.changeJobState(self.actionURL, 'PUT', post_data, ssl_verifyhost=False))
            return rslts
        elif jobid:
            self.server="https://%s:8443"%jobid.split('@')[-1]
            item = jobid
            if self.acctRole:
                self.actionURL = constants.JOBSUB_JOB_RELEASE_URL_PATTERN_WITH_ROLE\
                        % (self.server, self.acctGroup, self.acctRole, item)
            else:
                self.actionURL = constants.JOBSUB_JOB_RELEASE_URL_PATTERN\
                        % ( self.server, self.acctGroup, item )
            return self.changeJobState(self.actionURL, 'PUT', post_data, ssl_verifyhost=False)
        else:
            raise JobSubClientError("release requires either a jobid or uid")





    def hold(self, jobid=None, uid=None, constraint=None):
        jobid=self.checkID(jobid)
        post_data = [
            ('job_action', 'HOLD')
        ]
        if constraint:
            self.probeSchedds()
            rslts = []
            for schedd in self.schedd_list:
                srv = "https://%s:8443"%schedd
                self.actionURL = constants.JOBSUB_JOB_CONSTRAINT_URL_PATTERN \
                        % ( srv, self.acctGroup, urllib.quote(constraint) )
                if uid:
                    self.actionURL = "%s%s/" % (self.actionURL, uid)
                rslts.append(self.changeJobState(self.actionURL, 'PUT', post_data, ssl_verifyhost=False))
            return rslts
        elif uid:
            self.probeSchedds()
            rslts = []
            for schedd in self.schedd_list:
                srv = "https://%s:8443"%schedd
                item = uid
                if self.acctRole:
                    self.actionURL = constants.JOBSUB_JOB_HOLD_BYUSER_URL_PATTERN_WITH_ROLE\
                        % (srv, self.acctGroup, self.acctRole, item )
                else:
                    self.actionURL = constants.JOBSUB_JOB_HOLD_BYUSER_URL_PATTERN\
                        % ( srv, self.acctGroup, item )
                if jobid:
                    self.actionURL = "%s%s/" % (self.actionURL, jobid)
                rslts.append(self.changeJobState(self.actionURL, 'PUT', post_data, ssl_verifyhost=False))
            return rslts
        elif jobid:
            self.server="https://%s:8443"%jobid.split('@')[-1]
            item = jobid
            if self.acctRole:
                self.actionURL = constants.JOBSUB_JOB_HOLD_URL_PATTERN_WITH_ROLE\
                        % (self.server, self.acctGroup, self.acctRole, item )
            else:
                self.actionURL = constants.JOBSUB_JOB_HOLD_URL_PATTERN\
                        % ( self.server, self.acctGroup, item )
            return self.changeJobState(self.actionURL, 'PUT', post_data, ssl_verifyhost=False)
        else:
            raise JobSubClientError("hold requires one of a jobid or uid or constraint")



    
    def remove(self, jobid=None, uid=None, constraint=None):
        url_pattern = constants.remove_url_dict.get( (jobid is not None, 
                                                     uid is not None, 
                                                     self.acctRole is not None, 
                                                     self.forcex) )
        if constraint:
            self.probeSchedds()
            rslts = []
            for schedd in self.schedd_list:
                srv = "https://%s:8443"%schedd
                self.actionURL = constants.JOBSUB_JOB_CONSTRAINT_URL_PATTERN\
                        % ( srv, self.acctGroup, urllib.quote(constraint) )
                if uid:
                    self.actionURL = "%s%s/" % (self.actionURL, uid)
                rslts.append(self.changeJobState(self.actionURL, 'DELETE',  ssl_verifyhost=False))
            return rslts
        elif uid:
            item = uid
            self.probeSchedds()
            rslts = []
            for schedd in self.schedd_list:
                srv = "https://%s:8443"%schedd
                if self.acctRole:
                    self.actionURL = constants.JOBSUB_JOB_REMOVE_BYUSER_URL_PATTERN_WITH_ROLE\
                        % (srv, self.acctGroup, self.acctRole, item)
                else:
                    self.actionURL = constants.JOBSUB_JOB_REMOVE_BYUSER_URL_PATTERN\
                        % ( srv, self.acctGroup, item )
                if jobid:
                    self.actionURL = "%s%s/" % (self.actionURL, jobid)
                    if self.forcex:
                        self.actionURL = "%sforcex/" % (self.actionURL)
                rslts.append(self.changeJobState(self.actionURL, 'DELETE', ssl_verifyhost=False))
            return rslts
        elif jobid:
            jobid=self.checkID(jobid)
            self.server="https://%s:8443"%jobid.split('@')[-1]
            item = jobid
            if self.acctRole:
                self.actionURL = constants.JOBSUB_JOB_REMOVE_URL_PATTERN_WITH_ROLE\
                    % (self.server, self.acctGroup, self.acctRole, item)
            else:
                self.actionURL = constants.JOBSUB_JOB_REMOVE_URL_PATTERN\
                    % ( self.server, self.acctGroup, item )
            if self.forcex:
                self.actionURL = "%sforcex/" % (self.actionURL)
            return self.changeJobState(self.actionURL, 'DELETE', ssl_verifyhost=False)
        else:
            raise JobSubClientError("remove requires either a jobid or uid or constraint")




    def history(self, userid=None, jobid=None,outFormat=None):
        servers = get_jobsub_server_aliases(self.server)
        jobid = self.checkID(jobid)

        rc = 0
        for server in servers:
            self.histURL=constants.JOBSUB_HISTORY_URL_PATTERN  % (
                                                       server, self.acctGroup)
            if userid:
                self.histURL="%suser/%s/"%(self.histURL,userid)
            if jobid:
                self.histURL="%sjobid/%s/"%(self.histURL,jobid)
            qdate_ge=self.extra_opts.get('qdate_ge')
            if qdate_ge:
                qdate_ge = qdate_ge.replace(' ', '%20')
                self.histURL="%sqdate_ge/%s/"%(self.histURL,qdate_ge)
            qdate_le=self.extra_opts.get('qdate_le')
            if qdate_le:
                qdate_le = qdate_le.replace(' ', '%20')
                self.histURL="%sqdate_le/%s/"%(self.histURL,qdate_le)

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

    def serverAuthMethods(self, acct_group=None):
        
        if not acct_group:
            acct_group = self.acctGroup
        authMethodsURL = constants.JOBSUB_AUTHMETHODS_URL_PATTERN %\
                (self.server, acct_group)
        curl, response = curl_secure_context(authMethodsURL, self.credentials)
        curl.setopt(curl.SSL_VERIFYHOST, 0)
        curl.setopt(curl.CUSTOMREQUEST, 'GET' )
        try:
            curl.perform()
            http_code = curl.getinfo(pycurl.RESPONSE_CODE)
            r = response.getvalue()
            method_list = json.loads(response.getvalue())
            methods = []
            for m in method_list.get('out'):
                methods.append(str(m))
            if 'myproxy' in methods:
                
                cred = jobsubClientCredentials.cigetcert_to_x509(
                        self.initial_server,
                        acct_group,
                        self.verbose)
                if cred:
                    self.credentials['cert'] = cred
                    self.credentials['key'] = cred
                    self.credentials['proxy'] = cred
            return methods


        except pycurl.error, error:
            errno, errstr = error
            http_code = curl.getinfo(pycurl.RESPONSE_CODE)
            err = "HTTP response:%s PyCurl Error %s: %s" % (http_code,errno, errstr)
            #logSupport.dprint(traceback.format_exc(limit=10))
            traceback.print_stack()
            raise JobSubClientError(err)
        #except:
            #probably called a server that doesnt support this URL, just continue
            #and let round robin do its thing
            #err = "Error: %s "% sys.exc_info()[0]
            #logSupport.dprint(err)
            #raise 

        curl.close()
        response.close()


 
    def probeSchedds(self, ignore_secondary_schedds = True):
        """query all the schedds behind the jobsub-server.  Create a list of
        them stored in self.schedd_list and change self.server to point to
        the least loaded one"""
        listScheddsURL = constants.JOBSUB_SCHEDD_LOAD_PATTERN % (self.server)
        curl, response = curl_secure_context(listScheddsURL, self.credentials)
        curl.setopt(curl.CUSTOMREQUEST, 'GET' )
        best_schedd = self.server
        best_jobload = sys.maxsize
        try:
            curl.perform()
            http_code = curl.getinfo(pycurl.RESPONSE_CODE)
            r = response.getvalue()
            schedd_list = json.loads(response.getvalue())
            for line in schedd_list['out']:
                  pts = line.split()
                  if len(pts[:1]) and len(pts[-1:]):
                      schedd = pts[:1][0]
                      if schedd not in self.schedd_list:
                          self.schedd_list.append(schedd)
                      jobload = long(pts[-1:][0])
                      if schedd.find('@') > 0 and ignore_secondary_schedds:
                          continue
                      if jobload < best_jobload:
                          best_schedd = schedd
                          best_jobload = jobload
            #this will fail for secondary schedd with @ in name
            #so ignore_secondary_schedds must be true for now
            self.server = "https://%s:%s"%(best_schedd,self.serverPort)
        except pycurl.error, error:
            errno, errstr = error
            http_code = curl.getinfo(pycurl.RESPONSE_CODE)
            err = "HTTP response:%s PyCurl Error %s: %s" % (http_code,errno, errstr)
            #logSupport.dprint(traceback.format_exc(limit=10))
            traceback.print_stack()
            raise JobSubClientError(err)
        except:
            #probably called a server that doesnt support this URL, just continue
            #and let round robin do its thing
            logSupport.dprint( "Error: %s "% sys.exc_info()[0])
            pass

        curl.close()
        response.close()


    def listConfiguredSites(self):
        self.listURL=constants.JOBSUB_CONFIGURED_SITES_URL_PATTERN%\
                (self.server,self.acctGroup)
        return self.changeJobState(self.listURL,'GET')

    def listJobs(self, jobid=None, userid=None,outFormat=None):
        jobid=self.checkID(jobid)
        constraint = self.extra_opts.get('constraint')
        if constraint:
            self.listURL = constants.JOBSUB_JOB_CONSTRAINT_URL_PATTERN %\
                    (self.server, self.acctGroup, urllib.quote(constraint))
        elif self.better_analyze and jobid:
            self.listURL = constants.JOBSUB_Q_JOBID_BETTER_ANALYZE_URL_PATTERN%\
                    (self.server, jobid)
        elif self.better_analyze and not jobid:
            raise JobSubClientError("you must specify a jobid with --better-analyze")
        elif jobid is None and self.acctGroup is None and userid is None:
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
                                serving_server, response_time, verbose=self.verbose )
        else:
            print_formatted_response(value, code, self.server,
                                     serving_server, response_time, verbose=self.verbose)


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
    proxy = credentials.get('proxy')
    if proxy:
        # When using proxy set the CAINFO to the proxy so curl can correctly
        # pass the X509 credential chain to the server
        curl.setopt(curl.CAINFO, proxy)
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
    curl.setopt(curl.SSLVERSION, curl.SSLVERSION_TLSv1)

    return (curl, response)


def report_counts(msg):
    jobs = 0 
    completed = 0
    removed = 0
    idle = 0
    running = 0
    held = 0
    suspended = 0
    jjid_pattern = re.compile('^[0-9]+[.][0-9]+[@].*$')
    for line in msg:
        if jjid_pattern.match(line):
            jobs += 1
            if ' C  ' in line:
                completed += 1
            elif ' X  ' in line:
                removed += 1
            elif ' I  ' in line:
                idle += 1
            elif ' R  ' in line:
                running += 1
            elif ' H  ' in line:
                held += 1
            elif ' S  ' in line:
                suspended += 1
    if jobs:
        print "%s jobs; %s completed, %s removed, %s idle, %s running, %s held, %s suspended" %( jobs, completed, removed, idle, running, held, suspended) 

def print_msg(msg):
    signal(SIGPIPE,SIG_DFL)
    if isinstance(msg, (str, int, float, unicode)):
        print '%s' % (msg)
    elif isinstance(msg, (list, tuple)):
        for itm in msg:
            print itm
        report_counts(msg)
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
                        response_time, ignore_empty_msg=True, verbose=False):
    response_dict = json.loads(response)
    output = response_dict.get('out')
    error = response_dict.get('err')
    # Print output and error
    if output:
        print_msg(output)
        if verbose:
            print_server_details(response_code, server, serving_server, response_time)

    if error or not ignore_empty_msg:
        print 'RESPONSE ERROR:'
        print_msg(error)
        print_server_details(response_code, server, serving_server, response_time)

   

def print_formatted_response(msg, response_code, server, serving_server,
                             response_time, msg_type='OUTPUT',
                             ignore_empty_msg=True, print_msg_type=True, verbose=False):
    if ignore_empty_msg and not msg:
        return
    if print_msg_type:
        print 'Response %s:' % msg_type
    print_msg(msg)
    rsp = constants.HTTP_RESPONSE_CODE_STATUS.get(response_code)
    if rsp !='Success' or verbose:
        print_server_details(response_code, server, serving_server, response_time)


def get_client_credentials(acctGroup=None, server=None):
    """
    Client credentials lookup follows following order until it finds them

    Do not look for user certificate and key in ~/.globus directory. It
    typically contains encrypted key and we could not get the server
    communication to work with it.

    1. $X509_USER_PROXY
    2. $X509_USER_CERT & $X509_USER_KEY
    3. Default JOBSUB proxy location: /tmp/jobsub_x509up_u<UID>_<acctGroup>
       (we have been using a distinct JOBSUB proxy instead of the
       default /tmp/x509up_u<UID> since v0.4 , the default 
       was causing user side effects. We overlooked updating this
       comment.  )
    4. Kerberos ticket in $KRB5CCNAME. Convert it to proxy.
    5. Report failure
    """

    env_cert = None
    env_key = None
    cred_dict={}

    default_proxy_file = jobsubClientCredentials.default_proxy_filename(acctGroup)
    #print 'get_client_credentials default_proxy=%s' % default_proxy_file
    env_proxy = os.environ.get('X509_USER_PROXY')
    #print 'get_client_credentials env_proxy=%s' % env_proxy
    if env_proxy and os.path.exists(env_proxy):
        cred_dict['proxy'] = env_cert = env_key = env_proxy
    elif (os.environ.get('X509_USER_CERT') and os.environ.get('X509_USER_KEY')):
        env_cert = os.environ.get('X509_USER_CERT')
        env_key = os.environ.get('X509_USER_KEY')
    elif os.path.exists(default_proxy_file):
        cred_dict['proxy'] = default_proxy_file
        cred_dict['cert'] = default_proxy_file
        cred_dict['key'] = default_proxy_file
    if env_cert and env_key and os.path.exists(env_cert) and os.path.exists(env_key):
        cred_dict['cert'] = cred_dict['env_cert'] = env_cert
        cred_dict['key'] = cred_dict['env_key'] = env_key

    if cred_dict:
        x509 = jobsubClientCredentials.X509Credentials(
                cred_dict['cert'],
                cred_dict['key'])
        #if x509.expired():
        #    print "WARNING: %s has expired.  Attempting to regenerate " % \
        #            cred_dict['cert']
        #    cred_dict = {}
        if not x509.isValid():
            print "WARNING: %s is not valid.  Attempting to regenerate " %\
                    cred_dict['cert']
            cred_dict = {}

    if not cred_dict:
        long_err_msg = "Cannot find credentials to use. Try the following:\n"
        long_err_msg +="\n- If you have an FNAL kerberized "
        long_err_msg +="account, run 'kinit'.\n- Otherwise, if you have "
        long_err_msg +="an FNAL services account, run the following cigetcert "
        long_err_msg += "command and which \n will  prompt for your "
        long_err_msg += "services password, then resubmit your job:\n'cigetcert -s %s -o %s'"%(
            jobsubClientCredentials.server_hostname(server),
            jobsubClientCredentials.default_proxy_filename(acctGroup))
        long_err_msg += "\n- Otherwise, follow the instructions at "
        long_err_msg += "https://fermi.service-now.com/kb_view_customer.do?sysparm_article=KB0010798 "
        long_err_msg += "to obtain a services and/or kerberized account. "
        # Look for credentials in form of kerberos ticket
        try:
            krb5_creds = jobsubClientCredentials.Krb5Ticket()
        except jobsubClientCredentials.CredentialsNotFoundError:
            raise JobSubClientError(long_err_msg)
        if krb5_creds.isValid():
            jobsubClientCredentials.krb5cc_to_x509(
                    krb5_creds.krb5CredCache,
                    default_proxy_file)
            cred_dict['cert'] = default_proxy_file
            cred_dict['key'] = default_proxy_file
        else:
            raise JobSubClientError(long_err_msg)

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

def jid_callback(option, opt, value, p):
    if '@' not in value:
        sys.exit("jobid (%s) is missing an '@', it must be of the form number@server, i.e. 313100.0@fifebatch.fnal.gov"%value)
    setattr(p.values, option.dest, value)

def date_callback(option, opt, value, p):
    #check that date is valid and exit if conversion can't be made
    dateOK = False
    flist = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d' ]
    for fmt in flist:
        try:
            datetime.strptime(value,fmt)
            dateOK = True
            break
        except:
            pass
    if dateOK:
        setattr(p.values, option.dest, value)
    else:
        sys.exit("""invalid date format for '%s'.  Must be of the form 'YYYY-MM-DD' or 'YYYY-MM-DD hh:mm:ss'  example: '2015-03-01 01:59:03'"""%value)
    return p
