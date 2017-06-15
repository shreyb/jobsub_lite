#!/usr/bin/env python
"""
##########################################################################
# Project:
#   JobSub
#
# Author:
#   Parag Mhashilkar
#
# Description:
#   This module implements the JobSub client tool
#
##########################################################################
"""
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
    p = re.compile('\.rc[0-9]+$')
    if rel:
        rc = p.findall(rel)
        if rc:
            ver_str = '%s-%s' % (ver, rc[-1].replace('.', ''))

    return ver_str


class JobSubClientError(Exception):

    def __init__(self, errMsg="JobSub client action failed."):
        logSupport.dprint(traceback.format_exc())
        sys.exit(errMsg)


class JobSubClientSubmissionError(Exception):

    def __init__(self, errMsg="JobSub remote submission failed."):
        logSupport.dprint(traceback.format_exc())
        sys.exit(errMsg)


class JobSubClient:

    def __init__(self, server, acct_group, acct_role, server_argv,
                 dropboxServer=None, useDag=False,
                 extra_opts={}):
        self.server = server
        self.initial_server = server
        self.dropboxServer = dropboxServer
        self.account_group = acct_group
        self.server_argv = server_argv
        self.useDag = useDag
        self.serverPort = constants.JOBSUB_SERVER_DEFAULT_PORT
        self.extra_opts = extra_opts
        self.verbose = extra_opts.get('debug', False)
        self.better_analyze = extra_opts.get('better_analyze', False)
        self.forcex = extra_opts.get('forcex', False)
        self.schedd_list = []
        serverParts = re.split(':', self.server)
        if len(serverParts) != 3:
            if len(serverParts) == 1:
                self.server = "https://%s:%s" % (
                    serverParts[0], self.serverPort)
            if len(serverParts) == 2:
                if serverParts[0].find('http') >= 0:
                    self.server = "%s:%s:%s" % (serverParts[0],
                                                serverParts[1],
                                                self.serverPort)
                else:
                    self.server = "https://%s:%s" % (serverParts[0],
                                                     serverParts[1])
        else:
            if serverParts[2] != self.serverPort:
                self.serverPort = serverParts[2]
        self.credentials = get_client_credentials(acctGroup=self.account_group,
                                                  server=self.server)
        cert = self.credentials.get('env_cert', self.credentials.get('cert'))
        self.issuer = jobsubClientCredentials.proxy_issuer(cert)
        self.acct_role = get_acct_role(acct_role, cert)
        self.serverAuthMethods()

        # Help URL
        fmt_pattern = constants.JOBSUB_ACCTGROUP_HELP_URL_PATTERN
        self.help_url = fmt_pattern % (self.server,
                                       self.account_group)
        fmt_pattern = constants.JOBSUB_DAG_HELP_URL_PATTERN
        self.dag_help_url = fmt_pattern % (self.server,
                                           self.account_group)
        self.action_url = None
        self.submit_url = None
        self.dropbox_uri_map = {}
        self.directory_tar_map = {}
        self.job_executable = None
        self.job_exe_uri = None
        self.serverargs_b64en = None

    def init_submission(self):

        if self.server_argv:
            self.job_exe_uri = get_jobexe_uri(self.server_argv)
            self.job_executable = uri2path(self.job_exe_uri)
            d_idx = get_dropbox_idx(self.server_argv)
            if d_idx is not None and d_idx < len(self.server_argv):
                self.server_argv = self.server_argv[:d_idx] + \
                    self.server_argv[d_idx].split('=') + \
                    self.server_argv[d_idx + 1:]
            self.dropbox_uri_map = get_dropbox_uri_map(self.server_argv)
            self.get_directory_tar_map(self.server_argv)
            server_env_exports = get_server_env_exports(self.server_argv)
            srv_argv = copy.copy(self.server_argv)
            if not os.path.exists(self.job_executable):
                err = "You must supply a job executable, preceded by the "
                err += "directive 'file://' which is used to find the "
                err += "executable in jobsub_submit's  command line.  "
                err += "File '%s' not found. Exiting" % self.job_executable
                exe_in_tarball = False
                try:
                    dropbox_uri = get_dropbox_uri(self.server_argv)
                    if constants.DIRECTORY_SUPPORTED_URI in dropbox_uri:
                        dropbox_uri = self.directory_tar_map.get(dropbox_uri)

                    tarball = uri2path(dropbox_uri)
                    contents = tarfile.open(tarball, 'r').getnames()
                    if self.job_executable in contents or \
                            os.path.basename(self.job_executable) in contents:
                        exe_in_tarball = True
                    else:
                        for arg in self.server_argv:
                            if arg in contents or \
                                    os.path.basename(arg) in contents:
                                exe_in_tarball = True
                                break
                    if exe_in_tarball:
                        pass
                    else:
                        raise JobSubClientError(err)

                except:

                    raise JobSubClientError(err)

            if self.dropbox_uri_map:
                actual_server = self.server
                tfiles = []
                # upload the files
                result = self.dropbox_upload()
                # replace uri with path on server
                for idx in range(0, len(srv_argv)):
                    arg = srv_argv[idx]
                    if arg.find(constants.DROPBOX_SUPPORTED_URI) >= 0:
                        key = self.dropbox_uri_map.get(arg)
                        if key is not None:
                            values = result.get(key)
                            if values is not None:
                                if self.dropboxServer is None:
                                    srv_argv[idx] = values.get('path')
                                    actual_server = "https://%s:8443/" % \
                                        str(values.get('host'))
                                else:
                                    url = values.get('url')
                                    srv_argv[idx] = '%s%s' % \
                                        (self.dropboxServer, url)
                                if srv_argv[idx] not in tfiles:
                                    tfiles.append(srv_argv[idx])
                            else:
                                print "Dropbox upload failed with error:"
                                print json.dumps(result)
                                raise JobSubClientSubmissionError
                if len(tfiles) > 0:
                    transfer_input_files = ','.join(tfiles)
                    fmt_str = "export TRANSFER_INPUT_FILES=%s;%s"
                    server_env_exports = fmt_str % (transfer_input_files,
                                                    server_env_exports)
                    if self.dropboxServer is None and \
                            self.server != actual_server:
                        self.server = actual_server

            if self.job_exe_uri and self.job_executable:
                idx = get_jobexe_idx(srv_argv)
                if self.requiresFileUpload(self.job_exe_uri):
                    srv_argv[idx] = '@%s' % self.job_executable

            if server_env_exports:
                srv_env_export_b64en = \
                    base64.urlsafe_b64encode(server_env_exports)
                srv_argv.insert(0, '--export_env=%s' % srv_env_export_b64en)

            self.serverargs_b64en = base64.urlsafe_b64encode(
                ' '.join(srv_argv))

    def get_directory_tar_map(self, argv):

        for arg in argv:
            if arg.find(constants.DIRECTORY_SUPPORTED_URI) >= 0:
                tarpath = uri2path(arg)
                dirname = os.path.basename(tarpath)
                tarname = dirname + ".tar"
                create_tarfile(tarname, tarpath)
                digest = digest_for_file(tarname)
                tar_url = "dropbox://%s" % tarname
                self.dropbox_uri_map[tar_url] = digest
                self.directory_tar_map[arg] = tar_url

    def dropbox_upload(self):
        result = dict()
        post_data = list()
        orig_server = self.server
        self.probeSchedds()

        dropboxURL = constants.JOBSUB_DROPBOX_POST_URL_PATTERN %\
            (self.dropboxServer or self.server, self.account_group)

        # Create curl object and set curl options to use
        curl, response = curl_secure_context(dropboxURL, self.credentials)
        curl.setopt(curl.POST, True)
        if self.server != orig_server:
            curl.setopt(curl.SSL_VERIFYHOST, 0)

        # If it is a local file upload the file
        for file_name, key in self.dropbox_uri_map.items():
            post_data.append((key, (pycurl.FORM_FILE, uri2path(file_name))))
        curl.setopt(curl.HTTPPOST, post_data)
        response_time = 0
        try:
            stime = time.time()
            curl.perform()
            etime = time.time()
            response_time = etime - stime
        except pycurl.error as error:
            errno, errstr = error
            err = "PyCurl Error %s: %s" % (errno, errstr)
            # logSupport.dprint(traceback.format_exc())
            raise JobSubClientSubmissionError(err)

        response_code = curl.getinfo(pycurl.RESPONSE_CODE)
        response_content_type = curl.getinfo(pycurl.CONTENT_TYPE)
        serving_server = servicing_jobsub_server(curl)
        curl.close()

        if self.verbose:
            print "SERVER RESPONSE CODE: %s" % response_code
        value = response.getvalue()
        if response_content_type == 'application/json':
            result = json.loads(value)
        else:
            print_formatted_response(value, response_code, self.server,
                                     serving_server, response_time,
                                     verbose=self.verbose)
        if response_code == 200:
            response.close()
            return result
        else:
            import ast
            err = ast.literal_eval(value).get('err')
            if not err:
                err = value
            raise JobSubClientSubmissionError(err)

    def submit_dag(self):
        self.init_submission()
        if (not self.dropbox_uri_map) or self.dropboxServer:
            self.probeSchedds()
        self.serverAuthMethods()
        if self.acct_role:
            self.submit_url = \
                constants.JOBSUB_DAG_SUBMIT_URL_PATTERN_WITH_ROLE %\
                (self.server, self.account_group, self.acct_role)
        else:
            self.submit_url = constants.JOBSUB_DAG_SUBMIT_URL_PATTERN %\
                (self.server, self.account_group)
        krb5_principal = jobsubClientCredentials.krb5_default_principal()
        post_data = [
            ('jobsub_args_base64', self.serverargs_b64en),
            ('jobsub_client_version', version_string()),
            ('jobsub_client_krb5_principal', krb5_principal),
        ]

        logSupport.dprint('URL            : %s %s\n' %
                          (self.submit_url, self.serverargs_b64en))
        logSupport.dprint('CREDENTIALS    : %s\n' % self.credentials)
        logSupport.dprint('SUBMIT_URL     : %s\n' % self.submit_url)
        logSupport.dprint('SERVER_ARGS_B64: %s\n' %
                          base64.urlsafe_b64decode(self.serverargs_b64en))
        # cmd = 'curl -k -X POST -d jobsub_args_base64=%s %s' %\
        #        (self.serverargs_b64en, self.submit_url)

        # Get curl & resposne object to use
        curl, response = curl_secure_context(self.submit_url, self.credentials)

        # Set additional curl options for submit
        curl.setopt(curl.POST, True)
        # If we uploaded a dropbox file we saved the actual hostname to
        # self.server and self.submit_url so disable SSL_VERIFYHOST
        # if we select the best schedd we have to disable this
        curl.setopt(curl.SSL_VERIFYHOST, 0)

        # If it is a local file upload the file
        if self.requiresFileUpload(self.job_exe_uri):
            post_data.append(('jobsub_command',
                              (pycurl.FORM_FILE, self.job_executable)))
            payloadFileName = self.makeDagPayload(uri2path(self.job_exe_uri))
            post_data.append(('jobsub_payload',
                              (pycurl.FORM_FILE, payloadFileName)))
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
        except pycurl.error as error:
            errno, errstr = error
            http_code = curl.getinfo(pycurl.RESPONSE_CODE)
            err = "HTTP response:%s PyCurl Error %s: %s" % (http_code, errno,
                                                            errstr)
            # logSupport.dprint(traceback.format_exc())
            if errno == 60:
                err += "\nDid you remember to include the port number to "
                err += "your server specification \n( --jobsub-server %s )?" %\
                    self.server
            # logSupport.dprint(traceback.format_exc())
            raise JobSubClientSubmissionError(err)
        shutil.rmtree(os.path.dirname(payloadFileName), ignore_errors=True)

        self.printResponse(curl, response, response_time)
        curl.close()
        response.close()
        return http_code

    def makeDagPayload(self, infile):
        orig = os.getcwd()
        dirpath = tempfile.mkdtemp()
        fin = open(infile, 'r')
        z = fin.read()
        os.chdir(dirpath)
        fnameout = "%s" % (os.path.basename(infile))
        fout = open(fnameout, 'w')
        tar = tarfile.open('payload.tgz', 'w:gz')
        lines = z.split('\n')
        for line in lines:
            wrds = re.split('\s+', line)
            la = []
            for w in wrds:
                w2 = uri2path(w)
                if w != w2:
                    b = os.path.basename(w2)
                    w3 = " ${JOBSUB_EXPORTS} ./%s" % b
                    la.append(w3)
                    os.chdir(orig)
                    tar.add(uri2path(w), b)
                    os.chdir(dirpath)
                else:
                    la.append(w)
            la.append('\n')
            l2 = ' '.join(la)
            fout.write(l2)
        fin.close()
        fout.close()
        tar.add(fnameout, fnameout)
        tar.close()
        return "%s/payload.tgz" % dirpath

    def submit(self):
        self.init_submission()
        if (not self.dropbox_uri_map) or self.dropboxServer:
            self.probeSchedds()
        self.serverAuthMethods()

        if self.acct_role:
            self.submit_url = constants.JOBSUB_JOB_SUBMIT_URL_PATTERN_WITH_ROLE %\
                (self.server, self.account_group, self.acct_role)
        else:
            self.submit_url = constants.JOBSUB_JOB_SUBMIT_URL_PATTERN %\
                (self.server, self.account_group)
        krb5_principal = jobsubClientCredentials.krb5_default_principal()
        post_data = [
            ('jobsub_args_base64', self.serverargs_b64en),
            ('jobsub_client_version', version_string()),
            ('jobsub_client_krb5_principal', krb5_principal),
        ]

        logSupport.dprint('URL            : %s %s\n' %
                          (self.submit_url, self.serverargs_b64en))
        logSupport.dprint('CREDENTIALS    : %s\n' % self.credentials)
        logSupport.dprint('SUBMIT_URL     : %s\n' % self.submit_url)
        logSupport.dprint('SERVER_ARGS_B64: %s\n' %
                          base64.urlsafe_b64decode(self.serverargs_b64en))
        # cmd = 'curl -k -X POST -d jobsub_args_base64=%s %s' %\
        #       (self.serverargs_b64en, self.submit_url)

        # Get curl & resposne object to use
        curl, response = curl_secure_context(self.submit_url, self.credentials)

        # Set additional curl options for submit
        curl.setopt(curl.POST, True)
        # If we uploaded a dropbox file we saved the actual hostname to
        # self.server and self.submit_url so disable SSL_VERIFYHOST
        # always have to do this now as we select the best schedd
        # and submit directly to it
        curl.setopt(curl.SSL_VERIFYHOST, 0)

        # If it is a local file upload the file
        if self.requiresFileUpload(self.job_exe_uri):
            post_data.append(('jobsub_command',
                              (pycurl.FORM_FILE, self.job_executable)))
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
        except pycurl.error as error:
            errno, errstr = error
            http_code = curl.getinfo(pycurl.RESPONSE_CODE)
            err = "HTTP response:%s PyCurl Error %s: %s" % (http_code, errno,
                                                            errstr)
            if errno == 60:
                err += "\nDid you remember to include the port number to "
                err += "your server specification \n( --jobsub-server %s )?" %\
                    self.server
            # logSupport.dprint(traceback.format_exc())
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
        except pycurl.error as error:
            errno, errstr = error
            http_code = curl.getinfo(pycurl.RESPONSE_CODE)
            err = "HTTP response:%s PyCurl Error %s: %s" %\
                (http_code, errno, errstr)
            if errno == 60:
                err += "\nDid you remember to include the port number to "
                err += "your server specification \n( --jobsub-server %s )?" %\
                    self.server
            # logSupport.dprint(traceback.format_exc())
            raise JobSubClientError(err)

        self.printResponse(curl, response, response_time)
        curl.close()
        response.close()
        return http_code

    def checkID(self, jobid):
        return check_id(jobid)

    def release(self, jobid=None, uid=None, constraint=None):
        jobid = self.checkID(jobid)
        post_data = [
            ('job_action', 'RELEASE')
        ]
        if constraint:
            self.probeSchedds()
            rslts = []
            for schedd in self.schedd_list:
                srv = "https://%s:8443" % schedd
                acct = self.account_group
                if self.acct_role:
                    acct = "%s--ROLE--%s" % (acct, self.acct_role)
                self.action_url = constants.JOBSUB_JOB_CONSTRAINT_URL_PATTERN \
                    % (srv, acct, urllib.quote(constraint))
                if uid:
                    self.action_url = "%s%s/" % (self.action_url, uid)
                print "Schedd: %s" % schedd
                rslts.append(self.changeJobState(self.action_url,
                                                 'PUT',
                                                 post_data,
                                                 ssl_verifyhost=False))
            return rslts
        elif uid:
            self.probeSchedds()
            rslts = []
            item = uid
            _r_fmt = constants.JOBSUB_JOB_RELEASE_BYUSER_URL_PATTERN_WITH_ROLE
            for schedd in self.schedd_list:
                srv = "https://%s:8443" % schedd
                if self.acct_role:
                    u = _r_fmt \
                        % (srv, self.account_group, self.acct_role, item)
                    self.action_url = u
                else:
                    u = constants.JOBSUB_JOB_RELEASE_BYUSER_URL_PATTERN\
                        % (srv, self.account_group, item)
                    self.action_url = u
                if jobid:
                    self.action_url = "%s%s/" % (self.action_url, jobid)
                print "Schedd: %s" % schedd
                rslts.append(self.changeJobState(self.action_url,
                                                 'PUT',
                                                 post_data,
                                                 ssl_verifyhost=False))
            return rslts
        elif jobid:
            self.server = "https://%s:8443" % jobid.split('@')[-1]
            item = jobid
            if self.acct_role:
                u = constants.JOBSUB_JOB_RELEASE_URL_PATTERN_WITH_ROLE\
                    % (self.server, self.account_group, self.acct_role, item)
                self.action_url = u
            else:
                self.action_url = constants.JOBSUB_JOB_RELEASE_URL_PATTERN\
                    % (self.server, self.account_group, item)
            return self.changeJobState(self.action_url,
                                       'PUT',
                                       post_data,
                                       ssl_verifyhost=False)
        else:
            raise JobSubClientError("release requires either a jobid or uid")

    def hold(self, jobid=None, uid=None, constraint=None):
        jobid = self.checkID(jobid)
        post_data = [
            ('job_action', 'HOLD')
        ]
        if constraint:
            self.probeSchedds()
            rslts = []
            for schedd in self.schedd_list:
                srv = "https://%s:8443" % schedd
                acct = self.account_group
                if self.acct_role:
                    acct = "%s--ROLE--%s" % (acct, self.acct_role)
                self.action_url = constants.JOBSUB_JOB_CONSTRAINT_URL_PATTERN \
                    % (srv, acct, urllib.quote(constraint))
                if uid:
                    self.action_url = "%s%s/" % (self.action_url, uid)
                print "Schedd: %s" % schedd
                rslts.append(self.changeJobState(self.action_url,
                                                 'PUT',
                                                 post_data,
                                                 ssl_verifyhost=False))
            return rslts
        elif uid:
            self.probeSchedds()
            rslts = []
            for schedd in self.schedd_list:
                srv = "https://%s:8443" % schedd
                item = uid
                if self.acct_role:
                    u = constants.JOBSUB_JOB_HOLD_BYUSER_URL_PATTERN_WITH_ROLE\
                        % (srv, self.account_group, self.acct_role, item)
                    self.action_url = u
                else:
                    u = constants.JOBSUB_JOB_HOLD_BYUSER_URL_PATTERN\
                        % (srv, self.account_group, item)
                    self.action_url = u
                if jobid:
                    self.action_url = "%s%s/" % (self.action_url, jobid)
                print "Schedd: %s" % schedd
                rslts.append(self.changeJobState(self.action_url,
                                                 'PUT',
                                                 post_data,
                                                 ssl_verifyhost=False))
            return rslts
        elif jobid:
            self.server = "https://%s:8443" % jobid.split('@')[-1]
            item = jobid
            if self.acct_role:
                u = constants.JOBSUB_JOB_HOLD_URL_PATTERN_WITH_ROLE\
                    % (self.server, self.account_group, self.acct_role, item)
                self.action_url = u
            else:
                self.action_url = constants.JOBSUB_JOB_HOLD_URL_PATTERN\
                    % (self.server, self.account_group, item)
            return self.changeJobState(self.action_url,
                                       'PUT',
                                       post_data,
                                       ssl_verifyhost=False)
        else:
            err = "hold requires one of a jobid or uid or constraint"
            raise JobSubClientError(err)

    def remove(self, jobid=None, uid=None, constraint=None):
        url_pattern = constants.remove_url_dict.get((jobid is not None,
                                                     uid is not None,
                                                     self.acct_role is not None,
                                                     self.forcex))
        if constraint:
            self.probeSchedds()
            rslts = []
            for schedd in self.schedd_list:
                srv = "https://%s:8443" % schedd
                acct = self.account_group
                if self.acct_role:
                    acct = "%s--ROLE--%s" % (acct, self.acct_role)
                self.action_url = constants.JOBSUB_JOB_CONSTRAINT_URL_PATTERN\
                    % (srv, acct, urllib.quote(constraint))
                if uid:
                    self.action_url = "%s%s/" % (self.action_url, uid)
                print "Schedd: %s" % schedd
                rslts.append(self.changeJobState(
                    self.action_url, 'DELETE', ssl_verifyhost=False))
            return rslts
        elif uid:
            item = uid
            self.probeSchedds()
            rslts = []
            _user_fmt = constants.JOBSUB_JOB_REMOVE_BYUSER_URL_PATTERN
            _role_fmt = constants.JOBSUB_JOB_REMOVE_BYUSER_URL_PATTERN_WITH_ROLE
            for schedd in self.schedd_list:
                srv = "https://%s:8443" % schedd
                if self.acct_role:
                    self.action_url = _role_fmt \
                        % (srv, self.account_group, self.acct_role, item)
                else:
                    self.action_url = _user_fmt \
                        % (srv, self.account_group, item)
                if jobid:
                    self.action_url = "%s%s/" % (self.action_url, jobid)
                    if self.forcex:
                        self.action_url = "%sforcex/" % (self.action_url)
                print "Schedd: %s" % schedd
                rslts.append(self.changeJobState(
                    self.action_url, 'DELETE', ssl_verifyhost=False))
            return rslts
        elif jobid:
            _role_fmt = constants.JOBSUB_JOB_REMOVE_URL_PATTERN_WITH_ROLE
            jobid = self.checkID(jobid)
            self.server = "https://%s:8443" % jobid.split('@')[-1]
            item = jobid
            if self.acct_role:
                self.action_url = _role_fmt \
                    % (self.server, self.account_group, self.acct_role, item)
            else:
                self.action_url = constants.JOBSUB_JOB_REMOVE_URL_PATTERN\
                    % (self.server, self.account_group, item)
            if self.forcex:
                self.action_url = "%sforcex/" % (self.action_url)
            return self.changeJobState(self.action_url,
                                       'DELETE',
                                       ssl_verifyhost=False)
        else:
            raise JobSubClientError(
                "remove requires either a jobid or uid or constraint")

    def history(self, userid=None, jobid=None, outFormat=None):
        servers = get_jobsub_server_aliases(self.server)
        jobid = self.checkID(jobid)

        rc = 0
        for server in servers:
            hist_URL = constants.JOBSUB_HISTORY_URL_PATTERN % (
                server, self.account_group)
            if userid:
                hist_URL = "%suser/%s/" % (hist_URL, userid)
            if jobid:
                hist_URL = "%sjobid/%s/" % (hist_URL, jobid)
            qdate_ge = self.extra_opts.get('qdate_ge')
            if qdate_ge:
                qdate_ge = qdate_ge.replace(' ', '%20')
                hist_URL = "%sqdate_ge/%s/" % (hist_URL, qdate_ge)
            qdate_le = self.extra_opts.get('qdate_le')
            if qdate_le:
                qdate_le = qdate_le.replace(' ', '%20')
                hist_URL = "%sqdate_le/%s/" % (hist_URL, qdate_le)

            try:
                http_code = self.changeJobState(hist_URL, 'GET',
                                                ssl_verifyhost=False)
                rc += http_code_to_rc(http_code)
            except:
                print 'Error retrieving history from the server %s' % server
                rc += 1
                logSupport.dprint(traceback.format_exc())
        return rc

    def summary(self):
        list_url = constants.JOBSUB_Q_SUMMARY_URL_PATTERN % (self.server)
        return self.changeJobState(list_url, 'GET')

    def serverAuthMethods(self, acct_group=None):

        if not acct_group:
            acct_group = self.account_group
        auth_method_url = constants.JOBSUB_AUTHMETHODS_URL_PATTERN %\
            (self.server, acct_group)
        curl, response = curl_secure_context(auth_method_url, self.credentials)
        curl.setopt(curl.SSL_VERIFYHOST, 0)
        curl.setopt(curl.CUSTOMREQUEST, 'GET')
        curl.setopt(curl.CAPATH, get_capath())
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

        except pycurl.error as error:
            errno, errstr = error
            http_code = curl.getinfo(pycurl.RESPONSE_CODE)
            err = "HTTP response:%s PyCurl Error %s: %s" % (
                http_code, errno, errstr)
            # logSupport.dprint(traceback.format_exc(limit=10))
            # traceback.print_stack()
            raise JobSubClientError(err)
        # except:
            # probably called a server that doesnt support this URL, just continue
            # and let round robin do its thing
            #err = "Error: %s "% sys.exc_info()[0]
            # logSupport.dprint(err)
            # raise

        curl.close()
        response.close()

    def probeSchedds(self, ignore_secondary_schedds=True):
        """query all the schedds behind the jobsub-server.  Create a list of
        them stored in self.schedd_list and change self.server to point to
        the least loaded one"""
        #
        # test this, try to guard against unnecessary schedd queries
        if len(self.schedd_list):
            return
        best_schedd = self.server
        best_jobload = sys.maxsize
        try:
            listScheddsURL = constants.JOBSUB_SCHEDD_LOAD_PATTERN % (self.server)
            listScheddsURLacct = listScheddsURL + self.account_group + "/"
            try:
                curl, response = curl_secure_context(listScheddsURLacct, self.credentials)
                curl.setopt(curl.CUSTOMREQUEST, 'GET')
                curl.perform()
                http_code = curl.getinfo(pycurl.RESPONSE_CODE)
            except:
                curl, response = curl_secure_context(listScheddsURL, self.credentials)
                curl.setopt(curl.CUSTOMREQUEST, 'GET')
                curl.perform()
                http_code = curl.getinfo(pycurl.RESPONSE_CODE)

            #r = response.getvalue()
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
            # this will fail for secondary schedd with @ in name
            # so ignore_secondary_schedds must be true for now
            self.server = "https://%s:%s" % (best_schedd, self.serverPort)
            #print "best schedd is %s"%self.server
        except pycurl.error as error:
            errno, errstr = error
            http_code = curl.getinfo(pycurl.RESPONSE_CODE)
            err = "HTTP response:%s PyCurl Error %s: %s" % (
                http_code, errno, errstr)
            # logSupport.dprint(traceback.format_exc(limit=10))
            # traceback.print_stack()
            raise JobSubClientError(err)
        except:
            # probably called a server that doesnt support this URL, just continue
            # and let round robin do its thing
            logSupport.dprint("Error: %s " % sys.exc_info()[0])
            pass

        curl.close()
        response.close()

    def listConfiguredSites(self):
        """ jobsub_status --sites
        """
        list_url = constants.JOBSUB_CONFIGURED_SITES_URL_PATTERN %\
            (self.server, self.account_group)
        return self.changeJobState(list_url, 'GET')

    def listJobs(self, jobid=None, userid=None, outFormat=None):
        """ jobsub_q
        """
        jobid = self.checkID(jobid)
        constraint = self.extra_opts.get('constraint')
        if constraint:
            list_url = constants.JOBSUB_JOB_CONSTRAINT_URL_PATTERN %\
                (self.server, self.account_group, urllib.quote(constraint))
        elif self.better_analyze and jobid:
            list_url = constants.JOBSUB_Q_JOBID_BETTER_ANALYZE_URL_PATTERN %\
                (self.server, jobid)
        elif self.better_analyze and not jobid:
            err = "you must specify a jobid with --better-analyze"
            raise JobSubClientError(err)
        elif jobid is None and self.account_group is None and userid is None:
            list_url = constants.JOBSUB_Q_NO_GROUP_URL_PATTERN % self.server
        elif userid is not None:
            tmp_url = constants.JOBSUB_Q_USERID_URL_PATTERN %\
                (self.server, userid)
            if self.account_group is not None:
                tmp_url = "%sacctgroup/%s/" % (tmp_url, self.account_group)
            if jobid is not None:
                tmp_url = "%s%s/" % (tmp_url, jobid)
            list_url = tmp_url
        elif self.account_group is not None:
            tmp_url = constants.JOBSUB_Q_WITH_GROUP_URL_PATTERN %\
                (self.server, self.account_group)
            if jobid is not None:
                tmp_url = "%s%s/" % (tmp_url, jobid)
            list_url = tmp_url
        else:
            list_url = constants.JOBSUB_Q_JOBID_URL_PATTERN %\
                (self.server, jobid)

        if outFormat is not None:
            list_url = "%s%s/" % (list_url, outFormat)
        return self.changeJobState(list_url, 'GET')

    def requiresFileUpload(self, uri):
        """check uri to see if it is one
           of the types that requires a
           file upload to server.  Return
           False if it does not
        """
        if uri:
            protocol = '%s://' % (uri.split('://'))[0]
            if protocol in constants.JOB_EXE_SUPPORTED_URIs:
                return os.path.exists(uri2path(uri))
        return False

    def help(self, helpType='jobsubHelp'):
        """jobsub_submit --help or jobsub_submit_dag --help
        """
        help_url = self.help_url
        if helpType == 'dag':
            help_url = self.dag_help_url

        curl, response = curl_secure_context(help_url, self.credentials)
        return_value = None

        try:
            curl.perform()
        except pycurl.error as error:
            errno, errstr = error
            err = "PyCurl Error %s: %s" % (errno, errstr)
            # logSupport.dprint(err)
            # logSupport.dprint(traceback.format_exc())
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

        content_type, code, value, serving_server =\
            self.extractResponseDetails(curl, response)
        if self.extra_opts.get('jobid_output_only'):
            matchObj = re.match( r'(.*)Use job id (.*) to retrieve (.*)',
                       value, re.S|re.I)
            if matchObj and matchObj.group(2):
                print matchObj.group(2)
                return
        suppress_server_details = False
        if (self.extra_opts.get('uid')
                or self.extra_opts.get('constraint')) \
                and len(self.schedd_list) > 1:
            suppress_server_details = True

        if content_type == 'application/json':
            print_json_response(value,
                                code,
                                self.server,
                                serving_server,
                                response_time,
                                verbose=self.verbose,
                                suppress_server_details=suppress_server_details)
        else:
            print_formatted_response(value,
                                     code,
                                     self.server,
                                     serving_server,
                                     response_time,
                                     verbose=self.verbose,
                                     suppress_server_details=suppress_server_details)


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
            js_s = constants.JOBSUB_SERVER_URL_PATTERN % (
                socket.gethostbyaddr(ip)[0], p)
            aliases.add(js_s)

    if not aliases:
        # Just return the default one
        aliases.add(server)

    return aliases


def servicing_jobsub_server(curl):
    server = 'UNKNOWN'
    try:
        ip = curl.getinfo(pycurl.PRIMARY_IP)
        server = constants.JOBSUB_SERVER_URL_PATTERN %\
            (socket.gethostbyaddr(ip)[0],
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
        print "%s jobs; %s completed, %s removed, %s idle, %s running, %s held, %s suspended" % (jobs, completed, removed, idle, running, held, suspended)


def print_msg(msg):
    signal(SIGPIPE, SIG_DFL)
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
    print >> sys.stderr, 'JOBSUB SERVER RESPONSE CODE : %s (%s)' %\
        (response_code,
         constants.HTTP_RESPONSE_CODE_STATUS.get(response_code,
                                                 'Failed'))
    print >> sys.stderr, 'JOBSUB SERVER SERVICED IN   : %s sec' % response_time
    print >> sys.stderr, 'JOBSUB CLIENT FQDN          : %s' %\
        socket.gethostname()
    print >> sys.stderr, 'JOBSUB CLIENT SERVICED TIME : %s' %\
        time.strftime('%d/%b/%Y %X')


def print_json_response(response, response_code, server, serving_server,
                        response_time, suppress_server_details=False,
                        verbose=False):
    response_dict = json.loads(response)
    output = response_dict.get('out')
    error = response_dict.get('err')
    # Print output and error
    if output:
        print_msg(output)

    if error:
        if not verbose and 'all jobs matching constraint' in str(error):
            pass
        else:
            print "ERROR:"
            print_msg(error)

    if verbose or (error and not suppress_server_details):
        print_server_details(response_code, server,
                             serving_server, response_time)


def print_formatted_response(msg, response_code, server, serving_server,
                             response_time, msg_type='OUTPUT',
                             suppress_server_details=False, print_msg_type=True, verbose=False):
    if suppress_server_details and not msg:
        return
    if print_msg_type:
        print 'Response %s:' % msg_type
    print_msg(msg)
    rsp = constants.HTTP_RESPONSE_CODE_STATUS.get(response_code)
    if verbose or (rsp != 'Success' and not suppress_server_details):
        print_server_details(response_code, server,
                             serving_server, response_time)


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
    cred_dict = {}

    default_proxy_file = jobsubClientCredentials.default_proxy_filename(
        acctGroup)
    # print 'get_client_credentials default_proxy=%s' % default_proxy_file
    env_proxy = os.environ.get('X509_USER_PROXY')
    # print 'get_client_credentials env_proxy=%s' % env_proxy
    if env_proxy and os.path.exists(env_proxy):
        cred_dict['proxy'] = env_cert = env_key = env_proxy
    elif (os.environ.get('X509_USER_CERT') and os.environ.get('X509_USER_KEY')):
        env_cert = os.environ.get('X509_USER_CERT')
        env_key = os.environ.get('X509_USER_KEY')
    elif os.path.exists(default_proxy_file):
        cred_dict['proxy'] = default_proxy_file
        cred_dict['cert'] = default_proxy_file
        cred_dict['key'] = default_proxy_file
    if env_cert and \
            env_key and \
            os.path.exists(env_cert) and \
            os.path.exists(env_key):
        cred_dict['cert'] = cred_dict['env_cert'] = env_cert
        cred_dict['key'] = cred_dict['env_key'] = env_key

    if cred_dict:
        x509 = jobsubClientCredentials.X509Credentials(cred_dict['cert'],
                                                       cred_dict['key'])
        # if x509.expired():
        #    print "WARNING: %s has expired.  Attempting to regenerate " % \
        #            cred_dict['cert']
        #    cred_dict = {}
        if not x509.isValid():
            print "WARNING: %s is not valid.  Attempting to regenerate " %\
                cred_dict['cert']
            cred_dict = {}

    if not cred_dict:
        long_err_msg = "Cannot find credentials to use. Try the following:\n"
        long_err_msg += "\n- If you have an FNAL kerberized "
        long_err_msg += "account, run 'kinit'.\n- Otherwise, if you have "
        long_err_msg += "an FNAL services account, run the following cigetcert "
        long_err_msg += "command and which \n will  prompt for your "
        long_err_msg += "services password, then resubmit your job:\n'cigetcert -s %s -o %s'" % (
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
            jobsubClientCredentials.krb5cc_to_x509(krb5_creds.krb5CredCache,
                                                   default_proxy_file)
            cred_dict['cert'] = default_proxy_file
            cred_dict['key'] = default_proxy_file
        else:
            raise JobSubClientError(long_err_msg)

    return cred_dict


def get_capath():
    ca_dir_list = ['/etc/grid-security/certificates',
                   '/cvmfs/oasis.opensciencegrid.org/mis/certificates',
                   '/cvmfs/grid.cern.ch/etc/grid-security/certificates',
                   ]
    ca_dir = os.environ.get('X509_CERT_DIR')

    if (not ca_dir):
        for system_ca_dir in ca_dir_list:
            logSupport.dprint('checking %s' % system_ca_dir)
            if (os.path.exists(system_ca_dir)):
                ca_dir = system_ca_dir
                break

    if not ca_dir:
        err = 'Could not find CA Certificates in %s. ' % system_ca_dir
        err += 'Set X509_CERT_DIR in the environment.'
        raise JobSubClientError(err)

    logSupport.dprint('Using CA_DIR: %s' % ca_dir)
    return ca_dir


def create_tarfile(tar_file, tar_path, tar_type="tgz"):
    orig_dir = os.getcwd()
    logSupport.dprint('tar_file=%s tar_path=%s cwd=%s' %
                      (tar_file, tar_path, orig_dir))
    if tar_type == "tgz":
        tar = tarfile.open(tar_file, 'w:gz')
    else:
        tar = tarfile.open(tar_file, 'w:bz2')
    os.chdir(tar_path)
    tar_dir = os.getcwd()
    print('creating tar of %s' % tar_dir)
    failed_file_list = []
    f0 = os.path.realpath(tar_dir)
    files = os.listdir(tar_dir)

    for fname in files:
        f1 = os.path.join(f0, fname)
        try:
            tar.add(f1, fname)

        except:
            failed_file_list.append(fname)
    if len(failed_file_list) > 0:
        for fname in failed_file_list:
            print(
                "failed to add to tarfile: %s Permissions problem?\n" %
                fname)
    tar.close()
    os.chdir(orig_dir)

##########################################################################
# INTERNAL - DO NOT USE OUTSIDE THIS CLASS
##########################################################################


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
        idx = argv[i].find('=')
        if idx >= 0:
            arg = argv[i][:idx]
            val = argv[i][idx + 1:]
        else:
            arg = argv[i]
            val = None

        if arg in constants.JOBSUB_SERVER_OPT_ENV:
            if val is None:
                i += 1
                val = argv[i]
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
        if argv[i].find(constants.DROPBOX_SUPPORTED_URI) < 0 and\
                argv[i].find(constants.DIRECTORY_SUPPORTED_URI) < 0:
            i += 1
        else:
            return i

    return None


def get_dropbox_uri(argv):
    dropbox_idx = get_dropbox_idx(argv)
    dropbox_uri = None
    if dropbox_idx is not None:
        dropbox_uri = argv[dropbox_idx]
        if dropbox_uri.find('=') > 0:
            parts = dropbox_uri.split('=')
            for part in parts:
                if part.find(constants.DROPBOX_SUPPORTED_URI) >= 0:
                    dropbox_uri = part.strip()
                    return dropbox_uri
                if part.find(constants.DIRECTORY_SUPPORTED_URI) >= 0:
                    dropbox_uri = part.strip()
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
        if arg.find(constants.DROPBOX_SUPPORTED_URI) >= 0:
            map[arg] = digest_for_file(uri2path(arg))
    return map


def digest_for_file(fileName, block_size=2**20):
    dig = hashlib.sha1()
    f = open(fileName, 'r')
    while True:
        data = f.read(block_size)
        if not data:
            break
        dig.update(data)
    f.close()
    x = dig.hexdigest()
    return x


def check_id(jobid):
    if jobid is None:
        return jobid
    else:
        # p=re.compile('^[0-9]+\.*[0-9]*\@[\w]+-*_*[\w]*.fnal.gov$')
        p = re.compile('^[0-9]+\.*[0-9]*\@[\w]+[\w\-\_\.\@]*.fnal.gov$')
        if not p.match(jobid):
            err = "ERROR: --jobid '%s' is malformed" % jobid
            raise JobSubClientError(err)
        return jobid


def http_code_to_rc(http_code):
    if http_code >= 200 and http_code < 300:
        return 0
    return 1


def jid_callback(option, opt, value, p):
    if '@' not in value:

        err = "jobid (%s) is missing an '@', it must be of the " % value
        err += "form number@server, i.e. 313100.0@fifebatch.fnal.gov"
        sys.exit(err)
    setattr(p.values, option.dest, value)


def date_callback(option, opt, value, p):
    # check that date is valid and exit if conversion can't be made
    dateOK = False
    flist = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d']
    for fmt in flist:
        try:
            datetime.strptime(value, fmt)
            dateOK = True
            break
        except:
            pass
    if dateOK:
        setattr(p.values, option.dest, value)
    else:
        sys.exit(
            """invalid date format for '%s'.  Must be of the form 'YYYY-MM-DD' or 'YYYY-MM-DD hh:mm:ss'  example: '2015-03-01 01:59:03'""" %
            value)
    return p
