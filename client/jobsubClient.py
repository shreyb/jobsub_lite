#!/usr/bin/env python
import contextlib
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
import random
from datetime import datetime
from signal import signal, SIGPIPE, SIG_DFL
import subprocessSupport
from distutils import spawn
import argparse



class Version_String(argparse.Action):
    def __init__(self, 
                option_strings, 
                version=None, 
                dest=argparse.SUPPRESS, 
                default=argparse.SUPPRESS, 
                help="Show program's version number and exit"):
        super(Version_String, self).__init__(
                option_strings=option_strings,
                dest=dest,
                default=default,
                nargs=0,
                help=help)
        self.version = version

    def __call__(self, parser, namespace, values=None, option_string=None):
        version = self.version
        if version is None:
            version = version_string()
        formatter = parser._get_formatter()
        formatter.add_text(version)
        parser.exit(message=formatter.format_help())


def version_string():
    """ figure out response for --version commands
    """
    ver = constants.__rpmversion__
    rel = constants.__rpmrelease__

    ver_str = ver

    # Release candidates are in rpmrelease with specific pattern
    p = re.compile(r'\.rc[0-9]+$')
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


class JobSubClient(object):

    """ Definition of the class
    """

    def __init__(self, server, acct_group, acct_role, server_argv,
                 dropboxServer=None, useDag=False,
                 extra_opts={}):
        """An over-ambitious init class
           @server: the jobsub server fqdn (could be a load balancer,
                    will be determined later)
           @acct_group: condor accounting group, corresponds to
                        experiments at Fermilab
           @acct_role: VOMS role, typically Analyisis or Production
           @server_argv: list of arguments that client did not
                         recognize, pass them on to the jobsub server
           @dropboxServer:server to send payloads to that jobsub server or
                          jobs can then access
           @useDag: if True, submit a condor DAG
           @extra_opts: all the extra flags that the clients needed as new
                        features were added

        """
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
        self.dropbox_max_size = None
        self.dropbox_location = None
        self.ca_path = get_capath()
        if self.extra_opts.get('tarball_reject_list'):
            self.reject_list = read_re_file(
                self.extra_opts.get('tarball_reject_list'))
        else:
            self.reject_list = [
                # exclude .git and .svn directories
                r"\.git/",
                r"\.svn/",
                # exclude .core files
                r"\.core$",
                # exclude emacs backups
                r"\~.*$",
                # exclude pdfs and eps files
                r"\.pdf$",
                r"\.eps$",
                # NO PICTURES OF CATS
                r"\.png$",
                r"\.PNG$",
                r"\.gif$",
                r"\.GIF$",
                r"\.jpg$",
                r"\.jpeg$",
                r"\.JPG$",
                r"\.JPEG$",
                # no .log .out or .err files
                r"\.log$",
                r"\.err$",
                r"\.out$",
                # no tarfiles or zipfiles
                r"\.tar$",
                r"\.tgz$",
                r"\.zip$",
                r"\.gz$",
            ]

        constraint = self.extra_opts.get('constraint')
        uid = self.extra_opts.get('uid')
        if constraint and uid:
            if uid not in constraint:
                constraint = """Owner=?="%s"&&%s""" % (uid, constraint)
                self.extra_opts['constraint'] = constraint

        if len(serverParts) != 3:
            if len(serverParts) == 1:
                self.server = "https://%s:%s" % (
                    serverParts[0], self.serverPort)
                self.serverHost = serverParts[0]

            if len(serverParts) == 2:
                if serverParts[0].find('http') >= 0:
                    self.server = "%s:%s:%s" % (serverParts[0],
                                                serverParts[1],
                                                self.serverPort)
                    self.serverHost = serverParts[1].replace("//", "")
                else:
                    self.server = "https://%s:%s" % (serverParts[0],
                                                     serverParts[1])
                    self.serverHost = serverParts[0]
        else:
            if serverParts[2] != self.serverPort:
                self.serverPort = serverParts[2]
                self.serverHost = serverParts[1].replace("//", "")
        self.serverAliases = get_jobsub_server_aliases(self.server)
        self.credentials = get_client_credentials(acctGroup=self.account_group,
                                                  server=self.server)
        cert = self.credentials.get('env_cert', self.credentials.get('cert'))
        subject = jobsubClientCredentials.proxy_subject(cert)
        regex = re.compile('/CN=[0-9]+')
        # VerifyDepth = 10 -> 9 CN=/12323123/ chains fails
        if len(regex.findall(subject)) > 8:
            err = "\nERROR\n"
            err += """Your user proxy, %s has DN=%s .""" % (cert, subject)
            err += "  This probably means voms-proxy-init has been used to "
            err += "refresh it too many "
            err += " times.  The easist way to fix the problem is to remove "
            err += "the file %s and re-create it. The easiest way " % cert
            err += "to re-create it is to re-submit your job after "
            err += "removing the file."
            raise JobSubClientError(err)

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
        self.uploaded = {}
        self.job_executable = None
        self.job_exe_uri = None
        self.serverargs_b64en = None

    def init_submission(self):
        """ A refactor of __init__ ,
            only do this stuff if a job submission is requested
        """
        self.probeSchedds()

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

                except Exception:
                    raise JobSubClientError(err)

            if self.dropbox_uri_map:
                self.dropbox_location = self.dropboxLocation()
                self.dropbox_max_size = int(self.dropboxSize())
                actual_server = self.server
                tfiles = []
                # upload the files
                # if os.environ.get('JOBSUB_USE_CVMFS_TARBALLS'):
                if self.extra_opts.get('use_cvmfs_dropbox', False):
                    logSupport.dprint('calling dropbox_upload')
                    self.uploaded = self.dropbox_upload()
                    logSupport.dprint(
                        'dropbox_upload result=%s' %
                        self.uploaded)
                    if not self.uploaded:
                        raise JobSubClientSubmissionError(
                            'dropbox_upload failed')

                logSupport.dprint('calling ifdh_upload')
                result = self.ifdh_upload()
                self.uploaded.update(result)
                if not self.uploaded:
                    raise JobSubClientSubmissionError('ifdh_upload failed')

                for idx in range(0, len(srv_argv)):
                    arg = srv_argv[idx]
                    # tardir://
                    if arg.find(constants.DIRECTORY_SUPPORTED_URI) >= 0:
                        arg = self.directory_tar_map[arg]
                    # dropbox://
                    if arg.find(constants.DROPBOX_SUPPORTED_URI) >= 0:
                        key = self.dropbox_uri_map.get(arg)
                        if key is not None:
                            values = self.uploaded.get(key)
                            if values is not None:
                                srv_argv[idx] = values.get('path')
                                if srv_argv[idx] not in tfiles:
                                    if 'cid=' not in srv_argv[idx]:
                                        # print "DEBUG adding %s to tfiles" %
                                        # srv_argv[idx]
                                        tfiles.append(srv_argv[idx])
                            else:
                                print "Dropbox upload failed with error:"
                                print json.dumps(result)
                                raise JobSubClientSubmissionError
                if len(tfiles) > 0:
                    transfer_input_files = ','.join(tfiles)
                    fmt_str = "export PNFS_INPUT_FILES=%s;%s"
                    server_env_exports = fmt_str % (transfer_input_files,
                                                    server_env_exports)
                    if self.dropboxServer is None and \
                            self.server != actual_server:
                        self.server = actual_server

            # print "DEBUG 2 server_env_exports = %s" % server_env_exports
            # print "DEBUG 2 tfiles=%s"%tfiles
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
        """
        @argv: list of arguments to jobsub_* client command
               some of these are directories to be tarred up
               prefixed with tardir: i.e tardir://path/to/dir/
        foreach arg in argv:
            create somedir.tar from dir_url=tardir://path/to/somedir/
            compute digest of somedir.tar:
            create box_url = dropbox://somedir.tar

            set self.dropbox_uri_map[box_url] = digest
            sel self.directory_tar_map[dir_url] = box_url

        use these mapfiles later to get tarfiles to submitted jobs
        """
        for arg in argv:
            if arg.find(constants.DIRECTORY_SUPPORTED_URI) >= 0:  # tardir://
                dir_url = arg
                tarpath = uri2path(dir_url)
                if tarpath[-1] == '/':
                    tarpath = tarpath[:-1]
                dirname = os.path.basename(tarpath)
                tarname = dirname + ".tar"
                create_tarfile(tarname, tarpath, reject_list=self.reject_list)
                digest = digest_for_file(tarname)
                box_url = "dropbox://%s" % tarname
                self.dropbox_uri_map[box_url] = digest
                self.directory_tar_map[dir_url] = box_url
                logSupport.dprint("dropbox_uri_map=%s directory_tar_map=%s" %
                                  (self.dropbox_uri_map, self.directory_tar_map))

    def ifdh_upload(self):
        """
        upload files from dropbox_uri_map to dropbox_location
        via ifdh
        dropbox_uri_map has form:
        {'dropbox://annie_stuff.tar': 'd618fa5ff463c6e4070ebebc7bc0058e9b644d43'}

        RETURNS dictionary result of form after upload:
        {'d618fa5ff463c6e4070ebebc7bc0058e9b644d43':
        {'path': '/pnfs/annie/scratch/d618fa5ff463c6e4070ebebc7bc0058e9b644d43/annie_stuff.tar',
         'host': 'fermicloud042.fnal.gov'}}

        """

        result = {}
        os.environ['IFDH_CP_MAXRETRIES'] = "0"
        os.environ['GROUP'] = self.account_group
        os.environ['EXPERIMENT'] = self.account_group

        orig_dir = os.getcwd()
        # logSupport.dprint('self.directory_tar_map=%s'%self.directory_tar_map)
        # logSupport.dprint('self.dropbox_uri_map=%s'%self.dropbox_uri_map)

        for dropbox in self.dropbox_uri_map.iterkeys():
            # if we uploaded it to cvmfs don't re-upload
            # it to pnfs
            digest = self.dropbox_uri_map[dropbox]
            if digest in self.uploaded:
                continue
            val = {}
            srcpath = uri2path(dropbox)
            file_size = int(os.stat(srcpath).st_size)
            if file_size > self.dropbox_max_size:
                err = "%s is too large %s " % (srcpath, file_size)
                err += "max allowed size is %s " % self.dropbox_max_size
                err += "job submission failed"
                raise JobSubClientSubmissionError(err)

            # If we've tarred up the dir, we need to look in the CWD for
            # the tar file
            if dropbox in self.directory_tar_map.itervalues():
                srcpath = os.path.join(orig_dir, srcpath)

            destpath = os.path.join(self.dropbox_location,
                                    self.dropbox_uri_map[dropbox],
                                    os.path.basename(uri2path(dropbox)))

            # todo hardcoded a very fnal specific url here
            dpl = destpath.split('/')
            nfp = ["pnfs", "fnal.gov", "usr"]
            nfp.extend(dpl[2:])
            guc_path = '/'.join(nfp)
            globus_url_cp_cmd = ["globus-url-copy", "-rst-retries",
                                 "1", "-gridftp2", "-nodcau", "-restart", "-stall-timeout",
                                 "30", "-len", "16", "-tcp-bs", "16",
                                 "gsiftp://fndca1.fnal.gov/%s" % guc_path, "/dev/null", ]

            val['path'] = destpath
            val['host'] = self.server
            result[self.dropbox_uri_map[dropbox]] = val
            logSupport.dprint('srcpath=%s destpath=%s' % (srcpath, destpath))
            already_exists = False
            ifdh_exe = find_ifdh_exe()
            try:
                dropbox_dir = os.path.join(self.dropbox_location,
                                           self.dropbox_uri_map[dropbox])
                sts = "ifdh mkdir_p %s attempt: %s" %\
                    (dropbox_dir, '')
                logSupport.dprint(sts)
                cmd = "%s mkdir_p %s" % (ifdh_exe, dropbox_dir)
                subprocessSupport.iexe_cmd(cmd)
            except Exception as error:
                if 'File exists' in str(error):
                    pass
                else:
                    err = "%s mkdir %s failed: %s" %\
                        (ifdh_exe, os.path.join(self.dropbox_location,
                                                self.dropbox_uri_map[dropbox]), error)
                    logSupport.dprint(err)
                    raise JobSubClientError(err)
            try:
                sts = "ifdh cp %s %s attempt" % (srcpath, destpath)
                logSupport.dprint(sts)
                cmd = "%s cp %s %s" % (ifdh_exe, srcpath, destpath)
                subprocessSupport.iexe_cmd(cmd)
            except Exception as error:
                if 'File exists' in str(error):
                    already_exists = True
                else:
                    err = "%s cp %s %s failed: %s" % (
                        ifdh_exe, srcpath, destpath, error)
                    logSupport.dprint(err)
                    raise JobSubClientError(err)

            if already_exists and '/scratch/' in destpath:
                # read back 16 bytes of destfile to game the LRU in dcache
                # This is where IFDH automatically creates a voms proxy.
                # We'll unset X509_USER_PROXY later - we need this for
                # globus-url-copy
                try:
                    old_x509_user_proxy = os.environ['X509_USER_PROXY']
                except KeyError:
                    old_x509_user_proxy = None
                acct_role = self.acct_role if self.acct_role is not None else "Analysis"
                os.environ['X509_USER_PROXY'] = '/tmp/x509up_voms_%s_%s_%s' % \
                    (self.account_group, acct_role, os.getuid())

                try:
                    logSupport.dprint(
                        "executing: %s " %
                        (" ".join(globus_url_cp_cmd)))
                    subprocessSupport.iexe_cmd(" ".join(globus_url_cp_cmd))
                except Exception:
                    logSupport.dprint("%s failed %s" % (" ".join(globus_url_cp_cmd),
                                                        sys.exc_info()[1]))
                    logSupport.dprint(
                        "this globus error is usually not serious, proceeding")
                finally:
                    if old_x509_user_proxy is not None:
                        os.environ['X509_USER_PROXY'] = old_x509_user_proxy
                    else:
                        del os.environ['X509_USER_PROXY']

        return result

    def dropbox_upload(self):
        """
        upload files from dropbox_uri_map to dropbox_location
        to cvmfs server
        dropbox_uri_map has form:
        {'dropbox://annie_stuff.tar':'d618fa5ff463c6e4070ebebc7bc0058e9b644d43'}

        RETURNS dictionary result of form after upload:
        {'d618fa5ff463c6e4070ebebc7bc0058e9b644d43':
            {'path': 'cid=annie/d618fa5ff463c6e4070ebebc7bc0058e9b644d43,cdir=annie_stuff.tar',
             'host': 'distdev01.fnal.gov',}
         }

        """
        result = {}
        fmt = constants.JOBSUB_DROPBOX_CVMFS_SERVER_PATTERN

        dropbox_server_url = fmt % (self.server, self.account_group)
        try:
            self.dropboxServer = self.requestValue(dropbox_server_url)
            logSupport.dprint("self.dropboxServer=%s" % self.dropboxServer)
        except RuntimeError as err:
            msg = "failed to find cvmfs dropbox server"
            msg += str(err)
            raise JobSubClientSubmissionError(msg)

        for file_name, digest in self.dropbox_uri_map.items():
            if not is_tarfile(uri2path(file_name)):
                continue
            cdir = os.path.basename(uri2path(file_name))
            parts = cdir.split('.')
            if parts[-1] in ['tar', 'tgz']:
                cdir = '.'.join(parts[0:-1])
            if parts[-2] == 'tar':
                cdir = '.'.join(parts[0:-2])
            exists_url = []
            if isinstance(self.dropboxServer, list):

                for srv in self.dropboxServer:
                    exists_url.append(constants.JOBSUB_CID_EXISTS_URL_PATTERN %
                                      (srv, self.account_group, digest))
            else:
                exists_url.append(constants.JOBSUB_CID_EXISTS_URL_PATTERN %
                                  (self.dropboxServer, self.account_group, digest))
                dslist = []
                dslist.append(self.dropboxServer)
                self.dropboxServer = dslist

            logSupport.dprint('exists_url = %s' % exists_url)
            idx = 0
            exists = ''
            srv = None
            for url in exists_url:
                try:
                    resp = self.requestValue(url, 'GET')
                    if 'resp' in resp:
                        resp = resp['resp'].text
                    parts = resp.strip().split(':')
                    exists = parts[0]
                    path = parts[-1]
                    logSupport.dprint("url=%s exists='%s'" % (url,exists))
                    if exists == 'PRESENT':
                        srv = self.dropboxServer[idx]
                        break
                    if exists not in ['MISSING', 'OK']:
                        exists_url.remove(url)
                        del self.dropboxServer[idx]
                    idx += 1
                except Exception as err:
                    print "%s" % err
                    exists_url.remove(url)
                    del self.dropboxServer[idx]

            if not srv:
                srv = random.choice(self.dropboxServer)
            path = "%s/%s" % (self.account_group, digest)
            result[digest] = {'path': "cid=%s,cdir=%s" % (path, cdir),
                                  'host': srv,
                                  }
            if exists != 'PRESENT':
                upload_url = constants.JOBSUB_CID_PUBLISH_URL_PATTERN %\
                    (srv, self.account_group, digest)
                cert = self.credentials.get('cert')
                key = self.credentials.get('key')
                cmd = """curl --cert %s --key %s """ % (cert, key)
                cmd += """--url %s  -X POST --data-binary @%s """ % (upload_url,
                                                                     uri2path(file_name))
                try:
                    logSupport.dprint("cmd = %s" % cmd)
                    resp, err = subprocessSupport.iexe_cmd(cmd)
                    resp = resp.strip()
                    err = err.strip()
                    logSupport.dprint("resp = '%s'" % resp)
                    if resp not in ['OK', 'PRESENT']:
                        err += "failed to upload %s" % uri2path(file_name)
                        err += "\nto %s" % upload_url
                        for pt in resp, err:
                            err += "\noutput=%s" % pt
                        raise JobSubClientError(err)
                except RuntimeError as err:
                    raise JobSubClientError(err)

        return result


    def submit_dag(self):
        """ called from jobsub_submit_dag to uh well,
            submit a dag
        """
        self.init_submission()
        # if (not self.dropbox_uri_map) or self.dropboxServer:
        #    self.probeSchedds()
        # self.serverAuthMethods()
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

            post_data = self.post_data_append(post_data,
                                              'jobsub_command',
                                              pycurl.FORM_FILE,
                                              self.job_executable)
            payloadFileName = self.makeDagPayload(uri2path(self.job_exe_uri))

            post_data = self.post_data_append(post_data,
                                              'jobsub_payload',
                                              pycurl.FORM_FILE,
                                              payloadFileName)

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

    def post_data_append(self, post_data, payload, fmt, fname):
        """
        append payload to HTTP post_data payload
        Params:
            @post_data: list of http post data objects
            @payload
            @fmt is postdata format
            @fname is file to append
        """
        try:
            assert(os.access(fname, os.R_OK))
            post_data.append((payload, (fmt, fname)))
            return post_data
        except Exception:
            raise JobSubClientError(
                "error HTTP POSTing %s - Is it readable?" %
                fname)

    def makeDagPayload(self, infile):
        """ create a tarfile with all the files that
            go in a dag so it can be uploaded to the 
            jobsub server
            @infile: an xml input file for jobsub_submit_dag
        """
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
            wrds = re.split(r'\s+', line)
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
        """submit a job to jobsub server
           called by jobsub_submit client 
        """
        self.init_submission()
        # if (not self.dropbox_uri_map) or self.dropboxServer:
        #    self.probeSchedds()
        # self.serverAuthMethods()

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
            post_data = self.post_data_append(post_data,
                                              'jobsub_command',
                                              pycurl.FORM_FILE,
                                              self.job_executable)
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
                       ssl_verifyhost=True, connect_timeout=None):
        """
        perform job actions like remove/hold/release
        @url: REST API call to jobsub server that performs action
        @http_custom_request: ''POST', 'DELETE', etc
        @post_data: data to send with POST
        @ssl_verify_host: True or False, if True make sure the host
                          is who they claim they are
        @connect_timeout: how long to wait for server to return
                          response
        """

        http_code = 503 #service unavailable

        rtv = self.perform_(url, http_custom_request, post_data,
                            ssl_verifyhost, connect_timeout)
        if 'curl' in rtv:
            self.printResponse(rtv['curl'],
                               rtv['response'],
                               rtv['response_time'])
            rtv['curl'].close()
            rtv['response'].close()
            http_code = rtv['http_code']

        elif 'resp' in rtv:
            resp = rtv['resp']
            ses = rtv['session']
            http_code = resp.status_code
            self.print_response(resp, ses)
        
        elif 'error' in rtv:
            print rtv['error']

        return http_code

    def requestValue(self, url, http_custom_request='GET', post_data=None,
                     ssl_verifyhost=True, connect_timeout=None):
        """
        Retrieve values from jobsub server
        @url: REST API call to jobsub server that performs action
        @http_custom_request: 'GET' , no other requests make sense
                               in this context
        @post_data: unused? 
        @ssl_verify_host: True or False, if True make sure the host
                          is who they claim they are
        @connect_timeout: how long to wait for server to return
                          response
        """

        rtv = self.perform_(url, http_custom_request, post_data,
                            ssl_verifyhost, connect_timeout)

        if 'curl' in rtv:
            try:
                jsn = json.loads(rtv['response'].getvalue())
                val = jsn['out']
            except:
                try:
                    val = rtv['response'].getvalue()
                except Exception as err:
                    raise JobsubClientError(err)
            finally:
                rtv['curl'].close()
                rtv['response'].close()

        elif 'resp' in rtv:
            resp = rtv['resp']
            ses = rtv['session']
            try:
                doc = json.loads(resp.text)
                val = doc.get('out')
            except Exception as err:
                val = rtv
        elif 'error' in rtv:
            val = rtv['error']
        return val

    def perform_(self, url, http_custom_request, post_data=None,
                 ssl_verifyhost=True, connect_timeout=None):
        """
        Try to use requests library to send
        @url to jobsub server
        @http_custom_request: ''POST', 'DELETE', etc
        @post_data: data to send with POST
        @ssl_verify_host: True or False, if True make sure the host
                          is who they claim they are
        @connect_timeout: how long to wait for server to return
                          response

        if requests library not installed, complain and then use
        curl library
        """

        if os.environ.get('JOBSUB_USE_REQUESTLIB'):
            try:
                return self.perform_request(url, http_custom_request,
                                        post_data, ssl_verifyhost,
                                        connect_timeout)
            except ImportError:
                print "jobsub will be migrating to the requests library soon"
                print "open a service desk ticket to have python-requests installed"
                print "on this machine. "

        return self.perform_curl(url, http_custom_request,
                                 post_data, ssl_verifyhost,
                                 connect_timeout)

    def perform_curl(self, url, http_custom_request, post_data=None,
                     ssl_verifyhost=True, connect_timeout=None):
        """
        Generic curl API
        """
        r_dict = {}
        logSupport.dprint('ACTION URL     : %s\n' % url)
        logSupport.dprint('CREDENTIALS    : %s\n' % self.credentials)

        # Get curl & resposne object to use
        curl, response = curl_secure_context(url, self.credentials)
        r_dict['curl'] = curl
        r_dict['response'] = response
        curl.setopt(curl.CUSTOMREQUEST, http_custom_request)
        if post_data:
            curl.setopt(curl.HTTPPOST, post_data)
        if not ssl_verifyhost:
            curl.setopt(curl.SSL_VERIFYHOST, 0)
        if connect_timeout is not None:
            try:
                _timeout = int(connect_timeout)
            except ValueError:
                err = "timeout %s is not valid type (is %s, should be " +\
                    " %s "
                err = err % (connect_timeout, type(connect_timeout), "int")
                logSupport.dprint(err)
                raise JobSubClientError(err)
            else:
                curl.setopt(curl.CONNECTTIMEOUT, _timeout)

        http_code = 200
        response_time = 0
        try:
            stime = time.time()
            curl.perform()
            etime = time.time()
            response_time = etime - stime
            http_code = curl.getinfo(pycurl.RESPONSE_CODE)
            r_dict['response_time'] = response_time
            r_dict['http_code'] = http_code
        except pycurl.error as error:
            errno, errstr = error
            http_code = curl.getinfo(pycurl.RESPONSE_CODE)
            r_dict['http_code'] = http_code
            err = "HTTP response:%s PyCurl Error %s: %s" %\
                (http_code, errno, errstr)
            r_dict['error'] = err
            if errno == 7:
                etime = time.time()
                response_time = etime - stime
                r_dict['response_time'] = response_time
                return r_dict
                
            if errno == 60:
                err += "\nDid you remember to include the port number to "
                err += "your server specification \n( --jobsub-server %s )?" %\
                    self.server
            raise JobSubClientError(err)
        return r_dict

    def perform_request(self, url, http_custom_request, post_data=None,
                        ssl_verifyhost=True, connect_timeout=None):
        """
        Generic  python request lib interface
        """
        import requests

        logSupport.dprint('ACTION URL     : %s\n' % url)
        logSupport.dprint('CREDENTIALS    : %s\n' % self.credentials)
        my_hd = {'Accept': 'application/json'}

        http_code = 200
        response_time = 0
        r_dict = {}
        try:
            ses = requests.Session()
            r_dict['session'] = ses
            req = requests.Request(http_custom_request,
                                   url,
                                   data=post_data,
                                   headers=my_hd)
            prep = req.prepare()
            cred = (self.credentials.get('proxy'),
                    self.credentials.get('proxy')
                    )
            if not cred:
                cred = (self.credentials.get('cert'),
                        self.credentials.get('key')
                        )
            resp = ses.send(prep,
                            verify=ssl_verifyhost,
                            cert=cred,
                            timeout=connect_timeout)
            r_dict['resp'] = resp
        
        except requests.ConnectionError as error:
            r_dict['error'] =  error
        except Exception as error:
            print '%s' % error
            raise JobSubClientError(error)

        return r_dict


    def adjust_prio(self, jobid=None, uid=None):
        """ Adjust condor_prio for jobid or uid
            uid currently disabled in jobsub_prio
            actual priority value to adjust to comes
            from self.extra_opts['prio']
        """
        jobid = check_id(jobid)
        prio = self.extra_opts.get('prio')
        if not prio:
            err = 'you must supply a priority with --prio'
            raise JobsubClientError(err)

        post_data = [
            ('job_action', 'ADJUST_PRIO')
        ]
        if uid:
            self.probeSchedds()
            rslts = []
            _r_fmt = constants.JOBSUB_JOB_SUBMIT_URL_PATTERN_WITH_ROLE
            for schedd in self.schedd_list:
                srv = "https://%s:8443" % schedd
                if self.acct_role:
                    u = _r_fmt \
                        % (srv, self.account_group, self.acct_role)
                else:
                    u = constants.JOBSUB_JOB_SUBMIT_URL_PATTERN\
                        % (srv, self.account_group)
                u += 'setprio/%s/user/%s/' % (prio, uid)

                self.action_url = u
                rslts.append(self.changeJobState(self.action_url,
                                                 'PUT',
                                                 post_data,
                                                 ssl_verifyhost=False))
            return rslts
        elif jobid:
            self.server = "https://%s:8443" % jobid.split('@')[-1]
            if self.acct_role:
                u = constants.JOBSUB_JOB_SUBMIT_URL_PATTERN_WITH_ROLE\
                    % (self.server, self.account_group, self.acct_role)
            else:
                u = constants.JOBSUB_JOB_SUBMIT_URL_PATTERN\
                    % (self.server, self.account_group)

            u += 'setprio/%s/job_id/%s/' % (prio, jobid)
            #u += 'setprio/%s/1234@yak.fnal.gov/' % prio
            self.action_url = u
            return self.changeJobState(self.action_url,
                                       'PUT',
                                       post_data,
                                       ssl_verifyhost=False)

    def release(self, jobid=None, uid=None, constraint=None):
        """
        generate API call to server to do a condor_release
        called from jobsub_release client
        Params:
            @jobid: jobsubjobid (NNN.N@server.fnal.gov)
            @uid: user id
            @constraint: condor constraint
        """
        jobid = check_id(jobid)
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
        """
        generate API call to server to do a condor_hold
        called from jobsub_hold client
        Params:
            @jobid: jobsubjobid (NNN.N@server.fnal.gov)
            @uid: user id
            @constraint: condor constraint
        """
        jobid = check_id(jobid)
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
                                                 post_data=post_data,
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
                                                 post_data=post_data,
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
                                       post_data=post_data,
                                       ssl_verifyhost=False)
        else:
            err = "hold requires one of a jobid or uid or constraint"
            raise JobSubClientError(err)

    def remove(self, jobid=None, uid=None, constraint=None):
        """
        generate API call to server to do a condor_rm
        called from jobsub_rm client
        Params:
            @jobid: jobsubjobid (NNN.N@server.fnal.gov)
            @uid: user id
            @constraint: condor constraint
        """

        # url_pattern = constants.remove_url_dict.get((jobid is not None,
        #                                             uid is not None,
        #                                             self.acct_role is not None,
        #                                             self.forcex))
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
            jobid = check_id(jobid)
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
        """
        jobsub_history aka condor_history
        Params:
            @userid: unix user name
            @jobid: jobsubjobid
            @outFormat: not used, was for condor_history -l back
                        when this was a direct call to condor_history
                        it now goes to a sqlite database on the 
                        jobsub server for speedup 
        """
        jobid = check_id(jobid)
        self.probeSchedds()
        rc = 0
        for schedd in self.schedd_list:
            server = "https://%s:8443" % schedd
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
                                                ssl_verifyhost=True)
                rc += http_code_to_rc(http_code)
            except Exception:
                print 'Error retrieving history from the server %s' % server
                rc += 1
                logSupport.dprint(traceback.format_exc())
        return rc

    def summary(self):
        """
        jobsub_q --summary
        """
        list_url = constants.JOBSUB_Q_SUMMARY_URL_PATTERN % (self.server)
        return self.changeJobState(list_url, 'GET')

    def dropboxSize(self, acct_group=None):
        """Get max size of file allowed in dropbox location from server"""
        if not acct_group:
            acct_group = self.account_group

        dropbox_size_url = constants.JOBSUB_DROPBOX_MAX_SIZE_URL_PATTERN %\
            (self.server, acct_group)

        default_size = '1073741824'

        try:
            size = self.requestValue(dropbox_size_url)
            return size
        except Exception:
            return default_size

    def dropboxLocation(self, acct_group=None):
        """Get location of dropbox from server"""
        if not acct_group:
            acct_group = self.account_group

        dropbox_url = constants.JOBSUB_DROPBOX_LOCATION_URL_PATTERN %\
            (self.server, acct_group)
        try:
            location = self.requestValue(dropbox_url)
            return location
        except RuntimeError as error:
            raise JobSubClientError(error)

    def serverAuthMethods(self, acct_group=None):
        """
        Retrieve accepted authorization methods from jobsub-server
        URL to server is https://jobsub-server:(port)jobsub/acctgroups/%s/authmethods/
        Parameters:
            @acct_group (nova, mu2e etc) goes in %s of URL
        """
        if not acct_group:
            acct_group = self.account_group
        # check for down servers DNS RR
        for server in self.serverAliases:
            if is_port_open(server, self.serverPort):
                self.server = server
                break

        auth_method_url = constants.JOBSUB_AUTHMETHODS_URL_PATTERN %\
            (self.server, acct_group)

        methods = []
        try:
            method_list = self.requestValue(auth_method_url)
            for m in method_list:
                methods.append(str(m))
            need_cigetcert_methods = ['myproxy', 'ferry']
            for meth in need_cigetcert_methods:
                if meth in methods:
                    cred = jobsubClientCredentials.cigetcert_to_x509(
                        self.initial_server,
                        acct_group,
                        self.verbose)
                    if cred:
                        self.credentials['cert'] = cred
                        self.credentials['key'] = cred
                        self.credentials['proxy'] = cred
            return methods

        except RuntimeError as error:
            raise JobSubClientError(error)

    def probeSchedds(self, ignore_secondary_schedds=True):
        """query all the schedds behind the jobsub-server.  Create a list of
        them stored in self.schedd_list and change self.server to point to
        the least loaded one"""
        #
        # test this, try to guard against unnecessary schedd queries
        if len(self.schedd_list):
            return
        listScheddsURL = constants.JOBSUB_SCHEDD_LOAD_PATTERN % (self.server)
        if self.account_group:
            listScheddsURL = "%s%s/" % (listScheddsURL, self.account_group)

        best_schedd = self.server.replace("https://", "").split(":")[0]
        best_jobload = sys.maxsize
        condor_port = int(os.environ.get("JOBSUB_CONDOR_PORT", "9615"))
        try:
            schedd_list = self.requestValue(listScheddsURL)
            for line in schedd_list:
                pts = line.split()
                if len(pts[:1]) and len(pts[-1:]):
                    schedd = pts[:1][0]
                    if schedd.find('@') > 0 and ignore_secondary_schedds:
                        continue
                    if schedd not in self.schedd_list:
                        schedd_host = schedd.split('@')[-1]
                        if not is_port_open(schedd_host, self.serverPort):
                            err_fmt = 'ERROR jobsub server on %s port %s '
                            err_fmt += 'is not responding'
                            print err_fmt % (schedd_host, self.serverPort)
                        elif not is_port_open(schedd_host, condor_port):
                            print 'ERROR condor on  %s port %s not responding' %\
                                (schedd_host, condor_port)
                        else:
                            self.schedd_list.append(schedd)
                            jobload = long(pts[-1:][0])
                            if jobload < best_jobload:
                                best_schedd = schedd
                                best_jobload = jobload
            self.server = "https://%s:%s" % (best_schedd, self.serverPort)
        except RuntimeError as error:
            errno, errstr = err
            http_code = response.status_code
            raise JobSubClientError(err)

    def listConfiguredSites(self):
        """ jobsub_status --sites
        """
        list_url = constants.JOBSUB_CONFIGURED_SITES_URL_PATTERN %\
            (self.server, self.account_group)
        return self.changeJobState(list_url, 'GET')

    def listJobs(self, jobid=None, userid=None, outFormat=None):
        """ condor_q interface, called from jobsub_q
            Params:
                @jobid: jobsubjobid
                @userid: unix user name
                @outFormat: --long and --dag are currently supported
        """
        jobid = check_id(jobid)
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

        # We expect better-analyze queries to take longer, so give it 5 min
        if self.better_analyze:
            return self.changeJobState(url=list_url,
                                       http_custom_request='GET',
                                       connect_timeout=constants.JOBSUB_BETTER_ANALYZE_CONNECTTIMEOUT)

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

        return self.changeJobState(help_url, 'GET')

    def extractResponseDetails(self, curl, response):
        """
        Find some important details from HTTP response from jobsub-server
        return them as a tuple
        @parameter curl : pycurl object
        @parameter response: curl response object
        """
        content_type = curl.getinfo(pycurl.CONTENT_TYPE)
        code = curl.getinfo(pycurl.RESPONSE_CODE)
        value = response.getvalue()
        serving_server = servicing_jobsub_server(curl)
        return (content_type, code, value, serving_server)

    def print_response(self, response, session=None):
        """
        Given the requestlib response and session objects
        print response details to screen
        """
        if os.environ.get('DEBUG_REQUEST'):
            logSupport.dprint("dir response=%s" % dir(response))
            logSupport.dprint("response.headers=%s" % response.headers)
            if session:
                logSupport.dprint("dir session%s" % dir(session))
                logSupport.dprint("session.headers=%s" % session.headers)
        content_type = response.headers.get('content-type')
        code = response.status_code
        value = response.content
        serving_server = 'UNKNOWN'
        self.service_print_request(content_type,
                                   code,
                                   value,
                                   serving_server,
                                   response.elapsed)

    def printResponse(self, curl, response, response_time):
        """
        Given the curl and response objects print the response on screen
        """

        content_type, code, value, serving_server =\
            self.extractResponseDetails(curl, response)
        self.service_print_request(content_type,
                                   code,
                                   value,
                                   serving_server,
                                   response_time)

    def service_print_request(
            self, content_type, code, value, serving_server, response_time):
        """
        Do the actual printing to the screen from a printResponse(curl)
        or print_response(responselib) call to jobsub server
        """
        if self.extra_opts.get('jobid_output_only'):
            matchObj = re.match(r'(.*)Use job id (.*) to retrieve (.*)',
                                value, re.S | re.I)
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


def is_port_open(server, port):
    """ is @port on @server open?
    """
    is_open = False
    server = server.strip().replace('https://', '')
    sp = server.split(':')
    server = sp[0]
    if len(sp) == 2 and not port:
        port = sp[1]

    try:
        serverIP = socket.gethostbyname(server)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = s.connect_ex((serverIP, int(port)))
        s.close()
        if result == 0:
            is_open = True
    except Exception:
        pass
    return is_open


def get_jobsub_server_aliases(server):
    # Set of hosts in the HA mode
    aliases = []

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
            if is_port_open(socket.gethostbyaddr(ip)[0], p):
                aliases.append(js_s)

    if not aliases:
        # Just return the default one
        aliases.append(server)
    if len(aliases) > 1:
        random.shuffle(aliases)

    return aliases


def servicing_jobsub_server(curl):
    """
    Try to figure out which of the servers behind DNS RR is responding
    does not work with HAPROXY in front of servers
    """

    server = 'UNKNOWN'
    try:
        ip = curl.getinfo(pycurl.PRIMARY_IP)
        server = constants.JOBSUB_SERVER_URL_PATTERN %\
            (socket.gethostbyaddr(ip)[0],
             constants.JOBSUB_SERVER_DEFAULT_PORT)
    except Exception:        # Ignore errors. This is not critical
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
        cmd = '/usr/bin/voms-proxy-info -type -file %s' % proxy
        cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd)
        if 'RFC compliant proxy' in cmd_out:
            logSupport.dprint("setting CAINFO for %s" % proxy)
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
        print "%s jobs; %s completed, %s removed, %s idle, %s running, %s held, %s suspended" % (
            jobs, completed, removed, idle, running, held, suspended)


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
    """ all the gory details in CAPTIAL LETTERS.
    """
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
    """called by service_print_request if server returned json object
    """
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
                             suppress_server_details=False,
                             print_msg_type=True, verbose=False):
    """called by service_print_request if server returned text
    """
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
            cred_dict['proxy'] = default_proxy_file
        else:
            raise JobSubClientError(long_err_msg)

    return cred_dict


def get_capath():
    ca_dir_list = ['/etc/grid-security/certificates',
                   '/cvmfs/oasis.opensciencegrid.org/mis/certificates',
                   '/cvmfs/grid.cern.ch/etc/grid-security/certificates',
                   ]
    ca_dir = os.environ.get('X509_CERT_DIR')

    if not ca_dir:
        for system_ca_dir in ca_dir_list:
            if (os.path.exists(system_ca_dir)):
                ca_dir = system_ca_dir
                break

    if not ca_dir:
        err = 'Could not find CA Certificates in %s. ' % system_ca_dir
        err += 'Set X509_CERT_DIR in the environment.'
        raise JobSubClientError(err)

    logSupport.dprint('Using CA_DIR: %s' % ca_dir)
    return ca_dir


def create_tarfile(tar_file, tar_path, tar_type="tar", reject_list=[]):
    """
    create a compressed tarfile
        Args:
            tar_file (string): full pathname of tarfile to be created
            tar_path (string): directory to be tarred up into 'tar_file'
            tar_type (string, optional): if "tgz": gzipped tarfile
                                                  otherwise bzipped tarfile
            reject_list (list[]): list of regular expressions of file names
                                  to reject from the tar_file
        Returns:
            bool: True if successful, False otherwise.
        Raises:
            None
    """
    orig_dir = os.getcwd()
    logSupport.dprint('tar_file=%s tar_path=%s cwd=%s' %
                      (tar_file, tar_path, orig_dir))
    temp_name = tempfile.mktemp()

    tar = tarfile.open(temp_name, 'w')

    # dont tar old copies of tarball into new tarball
    if tar_file not in reject_list:
        reject_list.append('%s$' % tar_file)

    os.chdir(tar_path)
    tar_dir = os.getcwd()
    failed_file_list = []
    ftar_d = os.path.realpath(tar_dir)
    for root, dirs, files in os.walk(ftar_d):
        for dd in dirs:
            fd = os.path.join(root, dd)
            ok_include = True
            if os.path.islink(fd) or not os.listdir(fd):
                for patt in reject_list:
                    if re.search(patt, fd):
                        ok_include = False
                        break
                if ok_include:
                    try:
                        tar.add(fd[len(ftar_d) + 1:])
                    except Exception:
                        failed_file_list.append(fd)
        for ff in files:
            ok_include = True
            ft = os.path.join(root, ff)
            fname = os.path.basename(ft)
            for patt in reject_list:
                if re.search(patt, ft):
                    ok_include = False
                    break
            if ok_include:
                try:
                    tar.add(ft[len(ftar_d) + 1:])
                except Exception:
                    failed_file_list.append(fname)
    tar.close()
    cmd1 = "gzip -n %s" % temp_name
    subprocessSupport.iexe_cmd(cmd1)
    gzip_file = "%s.gz" % temp_name
    tar_file = os.path.join(orig_dir, tar_file)
    shutil.move(gzip_file, tar_file)
    os.chdir(orig_dir)
    if failed_file_list:
        for fname in failed_file_list:
            print(
                "failed to add to tarfile: %s Permissions problem?" %
                fname)
        return False
    return True


##########################################################################
# INTERNAL - DO NOT USE OUTSIDE THIS CLASS
##########################################################################


def get_acct_role(acct_role, proxy):
    """If no role is specified, try to extract it from VOMS proxy
    """
    role = acct_role
    if not role:
        voms_proxy = jobsubClientCredentials.VOMSProxy(proxy)
        if voms_proxy.fqan:
            match = re.search('/Role=(.*)/', voms_proxy.fqan[0])
            if match.group(1) != 'NULL':
                role = match.group(1)
    return role


def is_uri_supported(uri):
    """ is this uri one we handle?
    """
    protocol = '%s://' % (uri.split('://'))[0]
    if protocol in constants.JOB_EXE_SUPPORTED_URIs:
        return True
    return False


def get_server_env_exports(argv):
    """Any option -e should be extracted from the client and exported to the
       server appropriately.
       also --environment and --environment=
    """
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
    """
    Starting from the first arg parse the strings till you get one of the
    supported URIs that indicate the job exe.
    Skip the URI that follows certain options like -f which indicates input
    files to upload
    """
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
    """return index from @argv that contains the dropbox uri
    """

    i = 0
    while(i < len(argv)):
        if argv[i].find(constants.DROPBOX_SUPPORTED_URI) < 0 and\
                argv[i].find(constants.DIRECTORY_SUPPORTED_URI) < 0:
            i += 1
        else:
            return i

    return None


def get_dropbox_uri(argv):
    """ return the uri (path name) from the dropbox element
        in @argv
    """
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
    """return the name of the job executable
       from @argv
    """
    exe_idx = get_jobexe_idx(argv)
    job_exe = ''
    if exe_idx is not None:
        job_exe = argv[exe_idx]
    return job_exe


def uri2path(uri):
    """transform uri into path i.e:
       dropbox:///path/to/my/stuff =>
            /path/to/my/stuff
    """
    return re.sub(r'^.\S+://', '', uri)


def get_dropbox_uri_map(argv):
    """
    make a map with keys of file path and value of sequence
    """
    amap = dict()
    for arg in argv:
        if arg.find(constants.DROPBOX_SUPPORTED_URI) >= 0:
            amap[arg] = digest_for_file(uri2path(arg))
    return amap


def digest_for_file(file_name, block_size=2**20, write_chunks=False):
    """
    compute  sha1 digest or a file
        Args:
            file_name (str): file to be digested
            block_size (int): size of 'chunks' to be read from file_name
            write_chunks (bool): if True, create files of size 'block_size'
                in /tmp/(sha1_digest_of_file_name/) which can be re-assembled
                into a file with 'cat * > file_name' .  Chunks can be sized to
                spread across cacheing systems such as squid or dcache
        Returns:
            sha1 digest of file_name (string)
        Raises:
    """
    dig = hashlib.sha1()
    fhdl = open(file_name, 'r')
    block_size = int(block_size)
    if write_chunks:
        dirpath = tempfile.mkdtemp()
        dirtemp = os.path.dirname(dirpath)
        f_cnt = int('a00000', 16)
        # chunks will be named 'a00000, a00001, a00002, etc
        chunk_name = os.path.join(dirpath, str(hex(f_cnt))[2:])
    while True:
        data = fhdl.read(block_size)
        if not data:
            break
        dig.update(data)
        if write_chunks:
            chdl = open(chunk_name, 'wb')
            chdl.write(data)
            chdl.close()
            f_cnt += 1
            chunk_name = os.path.join(dirpath, str(hex(f_cnt))[2:])
    fhdl.close()
    hashd = dig.hexdigest()
    if write_chunks:
        newdir = os.path.join(dirtemp, hashd)
        if os.path.exists(newdir):
            shutil.rmtree(dirpath)
        else:
            os.rename(dirpath, newdir)
    return hashd


def find_ifdh_exe():
    """"
    dont just sit there, find it!
    """
    ifdh_exe = spawn.find_executable("ifdh.sh")
    if not ifdh_exe:
        here = os.path.dirname(os.path.realpath(__file__))
        if os.path.exists("%s/ifdh.sh" % here):
            ifdh_exe = "%s/ifdh.sh" % here
    return ifdh_exe


def check_id(jobid):
    """check that jobsubjobid is of correct form
        NNN.N@host.fnal.gov or
        NNN.N@schedd@host.fnal.gov
        TODO: probably shouldnt just be fnal.gov
    """
    if jobid is None:
        return jobid
    else:
        # p=re.compile('^[0-9]+\.*[0-9]*\@[\w]+-*_*[\w]*.fnal.gov$')
        p = re.compile(r'^[0-9]+\.*[0-9]*\@[\w]+[\w\-\_\.\@]*.fnal.gov$')
        if not p.match(jobid):
            err = "ERROR: --jobid '%s' is malformed" % jobid
            raise JobSubClientError(err)
        return jobid


def http_code_to_rc(http_code):
    """return 0 (unix shell true or OK) if
       http code within range, 
       return 1 otherwise
    """
    if http_code >= 200 and http_code < 300:
        return 0
    return 1


class JID_Callback(argparse.Action):
    def __call__(self, parser, namespace, value, option_string=None):
        if '@' not in value:
            err = "jobid (%s) is missing an '@', it must be of the " % value
            err += "form number@server, e.g. 313100.0@jobsub01.fnal.gov"
            sys.exit(err)
        setattr(namespace, self.dest, value)

class Date_Callback(argparse.Action):
    def __call__(self, parser, namespace, value, option_string=None):
        dateOK = False
        flist = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d']
        for fmt in flist:
            try:
                datetime.strptime(value, fmt)
                dateOK = True
                break
            except Exception:
                pass
        if dateOK:
            setattr(namespace, self.dest, value)
        else:
            sys.exit(
                """invalid date format for '%s'.  Must be of the form """ % value +
                """'YYYY-MM-DD' or 'YYYY-MM-DD hh:mm:ss'  """ +
                """example: '2015-03-01 01:59:03'""")


def is_tarfile(filename):
    """ well, is it?
    """
    if not os.path.exists(filename):
        return False
    return tarfile.is_tarfile(filename)


def read_re_file(filename):
    """ read and return a list from
        @filename: a list of python regular expressions
    """
    re_list = []
    f = open(filename, "r")
    lines = f.readlines()
    for line in lines:
        if line[0] != '#':
            re_list.append(line.rstrip('\n'))
    return re_list


@contextlib.contextmanager
def stdchannel_redirected(stdchannel, dest_filename):
    """
    A context manager to temporarily redirect stdout or stderr

    e.g.:


    with stdchannel_redirected(sys.stderr, os.devnull):
        if compiler.has_function('clock_gettime', libraries=['rt']):
            libraries.append('rt')
    """

    try:
        oldstdchannel = os.dup(stdchannel.fileno())
        dest_file = open(dest_filename, 'w')
        os.dup2(dest_file.fileno(), stdchannel.fileno())

        yield
    finally:
        if oldstdchannel is not None:
            os.dup2(oldstdchannel, stdchannel.fileno())
        if dest_file is not None:
            dest_file.close()


if __name__ == '__main__':
    # put anything you want to test without using the entire client here

    if len(sys.argv) == 1 or 'help' in sys.argv[1].lower():
        print "".join(("\n", "usage:", "\n",
                       "%s --help\n" % sys.argv[0],
                       "%s TEST_TAR_FUNCS output_tarfile " % sys.argv[0],
                       "input_directory[write_chunks (1|0)]  [block_size (int)]\n",
                       "%s TEST_DATE_CALLBACK 'date_string'\n" % sys.argv[0],))

    elif sys.argv[1] == "TEST_TAR_FUNCS":
        reject_list = ["\.git/", "\.svn/", "\.core$", "~$", "\.pdf$", "\.eps$", "\.png$",
                       "\.log$", "\.err$", "\.out$"]
        if len(sys.argv) >= 7:
            print 'reading reject_list file %s' % sys.argv[6]
            reject_list = read_re_file(sys.argv[6])
            print 'reject_list = %s' % reject_list

        create_tarfile(sys.argv[1 + 1], sys.argv[2 + 1],
                       reject_list=reject_list)
        WRITE_CHUNKS = False
        if len(sys.argv) >= 6:
            WRITE_CHUNKS = True
            DIG = digest_for_file(sys.argv[2],
                                  write_chunks=int(sys.argv[4]),
                                  block_size=int(sys.argv[5]))
        else:
            DIG = digest_for_file(sys.argv[2], write_chunks=int(sys.argv[4]))
        print "digest for %s is %s" % (sys.argv[2], DIG)
        if WRITE_CHUNKS:
            print "to test directory /tmp/%s contents use commands " % DIG
            print "'cat  /tmp/%s/* > %s.copy ; diff %s.copy  %s' " %\
                (DIG, sys.argv[2], sys.argv[2], sys.argv[2])
    elif sys.argv[1] == 'TEST_RE_LIST':
        x_re_list = read_re_file(sys.argv[2])
        print "re_list = %s" % x_re_list

    elif sys.argv[1] == "TEST_DATE_CALLBACK":
        def P_DUCK(): return None
        P_DUCK.values = lambda: None

        def OPT_DUCK(): return None
        OPT_DUCK.dest = "values"
        if date_callback(OPT_DUCK, None, sys.argv[2], P_DUCK):
            print "date format OK"

    else:
        print "syntax error for command input:  %s" % sys.argv
        print "try:  %s --help" % sys.argv[0]
