#!/usr/bin/env python
"""
 Description:
   This module implements the JobSub webapp authN/authZ functionailty.
   Some code and functionality is take from CDFCAF

 Project:
   JobSub

 Author:
   Parag Mhashilkar

 TODO:
   The code still has lot of hardcoded path and makes several assumptions.
   This needs to be cleaned up.

"""

import os
import sys
import cherrypy
import logger
import logging
import jobsub
import subprocessSupport
import authutils
import auth_myproxy
import auth_kca
import auth_gums

from functools import wraps, partial
from distutils import spawn
from JobsubConfigParser import JobsubConfigParser
from request_headers import get_client_dn
from request_headers import uid_from_client_dn


def authenticate(dn, acctgroup, acctrole):
    """Check which authentication method used by acctgroup
       and try that method

       Args:
                dn: DN of proxy or cert trying to authenticate
         acctgroup: accounting group (experiment)
          acctrole: role (Analysis, Production, etc)

    """
    methods = jobsub.get_authentication_methods(acctgroup)
    logger.log("Authentication method precedence: %s" % methods)
    for method in methods:
        cherrypy.response.status = 200
        logger.log("Authenticating using method: %s" % method)
        try:
            if method.lower() in ['gums', 'myproxy']:
                try:
                    username = auth_gums.authenticate(dn, acctgroup, acctrole)
                    cherrypy.request.username = username
                    return username
                except Exception as e:
                    logger.log('%s failed %s' % (method, e))
            elif method.lower() == 'kca-dn':
                try:
                    return auth_kca.authenticate(dn)
                except Exception as e:
                    logger.log('%s failed %s' % (method, e))
            else:
                logger.log("Unknown authenticate method: %s" % method)
        except Exception:
            logger.log("Failed to authenticate using method: %s" % method)

    err = "Failed to authenticate dn '%s' for group '%s' with role '%s' using known authentication methods" %\
        (dn, acctgroup, acctrole)
    logger.log(err, severity=logging.ERROR)
    logger.log(err, severity=logging.ERROR, logfile='error')
    raise authutils.AuthenticationError(dn, acctgroup)


def authorize(dn, username, acctgroup, acctrole=None, age_limit=3600):
    """Decide authorization method for acctgroup and
       try to call it

       Args:
                dn: DN of proxy or cert trying to authorize
          username: uid of user
         acctgroup: account group (experiment)
          acctrole: role (Analysis Production etc)
         age_limit: maximum age in seconds or existing proxy before
                    forced refresh
    """
    methods = jobsub.get_authentication_methods(acctgroup)
    logger.log("Authorizing method precedence: %s" % methods)
    for method in methods:
        cherrypy.response.status = 200
        logger.log("Authorizing using method: %s" % method)
        try:
            if method.lower() in ['gums', 'kca-dn']:
                try:
                    return auth_kca.authorize(dn, username,
                                              acctgroup, acctrole, age_limit)
                except Exception as e:
                    logger.log('authoriziation failed, %s' % e)

            elif method.lower() == 'myproxy':
                try:
                    return auth_myproxy.authorize(dn, username,
                                                  acctgroup, acctrole,
                                                  age_limit)
                except Exception as e:
                    logger.log('myproxy authoriziation failed, %s' % e)

            else:
                logger.log("Unknown authorization method: %s" % method)
        except Exception:
            logger.log("Failed to authorize using method: %s" % method)

    err = ''.join(["Failed to authorize dn '%s' " % dn,
                   "for group '%s' " % acctgroup,
                   "with role '%s' " % acctrole,
                   "using known authentication methods", ])
    logger.log(err, severity=logging.ERROR)
    logger.log(err, severity=logging.ERROR, logfile='error')
    raise authutils.AuthenticationError(dn, acctgroup)


def create_voms_proxy(dn, acctgroup, role):
    """create a VOMS proxy:
          first authenticate()
          then authorize()

       Args:
                dn: DN of proxy or cert trying to authenticate
         acctgroup: accounting group (experiment)
          acctrole: role (Analysis, Production, etc)

    """
    logger.log('create_voms_proxy: Authenticating DN: %s' % dn)
    username = authenticate(dn, acctgroup, role)
    logger.log('create_voms_proxy: Authorizing user: %s acctgroup: %s role: %s' % (
        username, acctgroup, role))
    voms_proxy = authorize(dn, username, acctgroup, role)
    logger.log('User authorized. Voms proxy file: %s' % voms_proxy)
    return (username, voms_proxy)


def refresh_pnfs_lru(agelimit=1):
    """refresh pnfs files staged to jobs in queue.
       called from cron
       Args:
           agelimit: if proxy is older than this value in seconds
                     then refresh
    """
    cmd = spawn.find_executable('condor_q')
    if not cmd:
        err = 'Unable to find condor_q in the PATH'
        logger.log(err, severity=logging.ERROR)
        logger.log(err, severity=logging.ERROR, logfile='error')
        raise Exception(err)
    cmd += """ -af:, "strcat(jobsub_group,string(\\".\\"),owner)" """
    cmd += """x509userproxysubject x509userproxy PNFS_INPUT_FILES -constraint"""
    cmd += """ "JobUniverse=?=5 && X509UserProxySubject=!=UNDEFINED  &&  """
    cmd += """ PNFS_INPUT_FILES=!=UNDEFINED" """
    # print "cmd = %s " % cmd
    logger.log(cmd, logfile='pnfs_refresh')
    already_processed = ['']
    queued_users = []
    refreshed_files = []
    cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd)
    if cmd_err:
        err = "command %s returned %s" % (cmd, cmd_err)
        logger.log(err, severity=logging.ERROR)
        logger.log(err, severity=logging.ERROR, logfile='pnfs_refresh')
        raise Exception(err)
    lines = sorted(cmd_out.split("\n"))
    supported_roles = JobsubConfigParser().supportedRoles()
    proxies = {}
    for line in lines:
        if line not in already_processed:
            already_processed.append(line)
            check = line.split(",")
            if len(check) >= 3:
                for i in range(len(check)):
                    check[i] = check[i].strip()
                try:
                    ac_grp = check[0]
                    dn = check[1]
                    grp, user = ac_grp.split(".")
                    if user not in queued_users:
                        queued_users.append(user)
                    grp = grp.replace("group_", "")
                    proxy_name = os.path.basename(check[2])
                    long_proxy_name = check[2]
                    pfn = proxy_name.split('_')
                    role = ''
                    if pfn[-1] in supported_roles:
                        role = pfn[-1]
                    elif pfn[-2] in supported_roles:
                        role = pfn[-2]
                    if long_proxy_name not in proxies:
                        proxies[long_proxy_name] = authorize(
                            dn, user, grp, role, agelimit)
                    for destpath in check[3:]:
                        if destpath not in refreshed_files and '/scratch/' in destpath:
                            refreshed_files.append(destpath)

                            # todo hardcoded a very fnal specific url here
                            dpl = destpath.split('/')
                            nfp = ["pnfs", "fnal.gov", "usr"]
                            nfp.extend(dpl[2:])
                            guc_path = '/'.join(nfp)
                            globus_url_cp_cmd = ["globus-url-copy", "-rst-retries",
                                                 "3", "-gridftp2", "-nodcau", "-restart", "-stall-timeout",
                                                 "60", "-len", "16", "-tcp-bs", "16",
                                                 "gsiftp://fndca1.fnal.gov/%s" % guc_path,
                                                 "/dev/null", ]
                            child_env = os.environ.copy()
                            child_env['X509_USER_PROXY'] = proxies[long_proxy_name]
                            child_env['X509_USER_CERT'] = proxies[long_proxy_name]
                            child_env['X509_USER_KEY'] = proxies[long_proxy_name]
                            try:
                                logger.log(
                                    " ".join(globus_url_cp_cmd), logfile='pnfs_refresh')
                                subprocessSupport.iexe_cmd(" ".join(globus_url_cp_cmd),
                                                           child_env=child_env)
                            except Exception:
                                err = "Error %s:%s" % (" ".join(globus_url_cp_cmd),
                                                       sys.exc_info()[1])
                                print err
                                logger.log(
                                    err, severity=logging.ERROR, logfile='pnfs_refresh')

                except Exception:
                    err = "Error processing %s:%s" % (line, sys.exc_info()[1])
                    print err
                    logger.log(err, severity=logging.ERROR)
                    logger.log(
                        err,
                        severity=logging.ERROR,
                        logfile='pnfs_refresh')

    # print 'removing proxies'
    for key in proxies:
        if os.path.exists(proxies[key]):
            # print 'removing %s'%proxies[key]
            os.remove(proxies[key])


def test():
    print 'test'


if __name__ == '__main__':
    #
    # Entry point for krbrefresh cron job.
    #
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test':
            test()
        elif sys.argv[1] == '--refresh-pnfs':
            refresh_pnfs_lru()
