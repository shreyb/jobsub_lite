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

from functools import wraps, partial
from distutils import spawn
from JobsubConfigParser import JobsubConfigParser


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
                    import auth_gums
                    return auth_gums.authenticate(dn, acctgroup, acctrole)
                except Exception as e:
                    logger.log('%s failed %s' % (method, e))
            elif method.lower() == 'kca-dn':
                try:
                    import auth_kca
                    return auth_kca.authenticate(dn)
                except Exception as e:
                    logger.log('%s failed %s' % (method, e))
            else:
                logger.log("Unknown authenticate method: %s" % method)
        except:
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
                    import auth_kca
                    return auth_kca.authorize(dn, username,
                                              acctgroup, acctrole, age_limit)
                except Exception as e:
                    logger.log('authoriziation failed, %s' % e)

            elif method.lower() == 'myproxy':
                try:
                    import auth_myproxy
                    return auth_myproxy.authorize(dn, username,
                                                  acctgroup, acctrole,
                                                  age_limit)
                except Exception as e:
                    logger.log('myproxy authoriziation failed, %s' % e)

            else:
                logger.log("Unknown authorization method: %s" % method)
        except:
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


def refresh_proxies(agelimit=3600):
    """refresh proxies for all jobs in queue.
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
    cmd += authutils.krbrefresh_query_fmt()
    already_processed = ['']
    queued_users = []
    cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd)
    if cmd_err:
        err = "command %s returned %s" % (cmd, cmd_err)
        logger.log(err, severity=logging.ERROR)
        logger.log(err, severity=logging.ERROR, logfile='error')
        raise Exception(err)
    lines = cmd_out.split("\n")
    for line in lines:
        if line not in already_processed:
            already_processed.append(line)
            check = line.split(",")
            if len(check) == 3:
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
                    x, uid, role = proxy_name.split('_')
                    print "checking proxy %s %s %s %s" % (dn, user, grp, role)
                    authorize(dn, user, grp, role, agelimit)
                except:
                    err = "Error processing %s:%s" % (line, sys.exc_info()[1])
                    logger.log(err, severity=logging.ERROR)
                    logger.log(err, severity=logging.ERROR, logfile='error')
    # todo: invalidate old proxies
    # one_day_ago=int(time.time())-86400
    # condor_history -format "%s^" accountinggroup \
    #-format "%s^" x509userproxysubject -format "%s\n" owner \
    #-constraint 'EnteredCurrentStatus > one_day_ago'
    # can be checked against already_processed list to remove x509cc_(user)
    # if user not in queued_users remove krb5cc_(user) and (user).keytab


def copy_user_krb5_caches():
    jobsubConfig = jobsub.JobsubConfig()
    krb5cc_dir = jobsubConfig.krb5ccDir
    cmd = spawn.find_executable('condor_q')
    if not cmd:
        raise Exception('Unable to find condor_q in the PATH')
    cmd += """ -format '%s\n' 'ifthenelse (EncrypInputFiles=?=UNDEFINED, string(EncryptInputFiles),string(""))' """
    already_processed = ['']
    cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd)
    if cmd_err:
        logger.log("%s" % sys.exc_info()[1])
        raise Exception("command %s returned %s" % (cmd, cmd_err))
    lines = set(cmd_out.split("\n"))
    for job_krb5_cache in lines:
        if job_krb5_cache not in already_processed:
            already_processed.append(job_krb5_cache)
            cache_basename = os.path.basename(job_krb5_cache)
            base_parts = cache_basename.split('_')
            username = base_parts[-1]
            system_cache_fname = os.path.join(krb5cc_dir, cache_basename)
            try:
                logger.log('copying %s to %s' %
                           (system_cache_fname, job_krb5_cache))
                jobsub.copy_file_as_user(
                    system_cache_fname, job_krb5_cache, username)
            except:
                logger.log("Error processing %s" % job_krb5_cache)
                logger.log("%s" % sys.exc_info()[1])


def get_client_dn():
    """
    Identify the client DN based on if the client is using a X509 cert-key
    pair or an X509 proxy. Currently only works with a single proxy chain.
    Wont work if the proxy is derieved from the proxy itself.
    """

    issuer_dn = cherrypy.request.headers.get('Ssl-Client-I-Dn')
    dn = client_dn = cherrypy.request.headers.get('Ssl-Client-S-Dn')

    # In case of proxy additional last part will be of the form /CN=[0-9]*
    # In other words, issuer_dn is a substring of the client_dn
    if client_dn.startswith(issuer_dn):
        dn = issuer_dn
    return dn


def _check_auth(dn, acctgroup, role):
    """Private method  @check_auth decorator uses to call out
       to create_voms_proxy, which calls authenticate() and
       then authorize()
    """
    return create_voms_proxy(dn, acctgroup, role)


def check_auth(func=None, pass_through=None):
    """ Implementation/entry point  of the @check_auth decorator.
        This decorator does  the authentication in the
        rest of the server/webapp python files
    """
    if func is None:
        return partial(check_auth, pass_through=pass_through)

    @wraps(func)
    def wrapper(*args, **kwargs):

        # see #8186, we need to be able to turn off authorization for certain http
        # requests until we can restructure the code
        #
        if pass_through and cherrypy.request.method in pass_through:
            logger.log(
                "returning without checking authorization per request for http methods %s" % pass_through)
            return func(*args, **kwargs)

        acctgroup = kwargs.get('acctgroup')
        logger.log(traceback=True)
        logger.log("args = %s kwargs=%s " % (args, kwargs))
        logger.log("request method=%s" % cherrypy.request.method)
        dn = get_client_dn()
        err = ''
        if dn and acctgroup:
            logger.log('DN: %s, acctgroup: %s ' % (dn, acctgroup))
            try:
                #role = 'Analysis'
                role = jobsub.default_voms_role(acctgroup)
                #logger.log('default voms role:%s' % role)
                tokens = acctgroup.split('--ROLE--')
                if len(tokens) > 1:
                    (acctgroup, role) = tokens[0:2]
                    kwargs['acctgroup'] = acctgroup
                    logger.log('found ROLE %s in %s' % (role, tokens))

                default_roles = ['Analysis',
                                 'Calibration', 'Data', 'Production']
                supported_roles = JobsubConfigParser().supportedRoles()
                if not supported_roles:
                    supported_roles = default_roles
                if role not in supported_roles:
                    err = "User authorization has failed: --role "
                    err += "'%s' not found. Configured roles are " % (role)
                    err += "%s . Check case and spelling." % supported_roles
                    cherrypy.response.status = 401
                    logger.log(err)
                    return {'err': err}

                supported_groups = JobsubConfigParser().supportedGroups()
                if acctgroup not in supported_groups:
                    err = "User authorization has failed: --group "
                    err += "'%s' not found. Configured groups are " % (
                        acctgroup)
                    err += "%s . Check case and spelling." % supported_groups
                    cherrypy.response.status = 401
                    logger.log(err)
                    return {'err': err}

                username, voms_proxy = _check_auth(dn, acctgroup, role)
                if username and voms_proxy:
                    kwargs['role'] = role
                    kwargs['username'] = username
                    kwargs['voms_proxy'] = voms_proxy
                    return func(*args, **kwargs)
                else:
                    # return error for failed auth
                    err = 'User authorization has failed: %s' % sys.exc_info()[
                        1]
                    cherrypy.response.status = 401
                    logger.log(err)
                    rc = {'err': err}
            except:
                # return error for failed auth
                err = 'User authorization has failed: %s' % sys.exc_info()[1]
                cherrypy.response.status = 401
                logger.log(err)
                rc = {'err': err}
        else:
            # return error for no subject_dn and acct group
            err = 'User has not supplied subject DN and/or accounting group:%s' % sys.exc_info()[
                1]
            logger.log(err)
            rc = {'err': err}
            cherrypy.response.status = 401
        return rc

    return wrapper


def test():
    """Test module
    """
    dns = {
        'fermilab': '/DC=gov/DC=fnal/O=Fermilab/OU=People/CN=Parag A. Mhashilkar/CN=UID:parag',
        'nova': '/DC=gov/DC=fnal/O=Fermilab/OU=People/CN=Parag A. Mhashilkar/CN=UID:',
        'mu2e': '/DC=gov/DC=fnal/O=Fermilab/OU=People/CN=Parag A. Mhashilkar',
        'minos': '/DC=gov/DC=fnal/O=Fermilab/OU=/CN=Parag A. Mhashilkar/CN=UID:parag',
        'minerva': '/DC=gov/DC=fnal/O=Fermilab/OU=/CN=Parag A. Mhashilkar/CN=UID',
    }

    for group in dns:
        try:
            create_voms_proxy(dns[group], group, 'Analysis')
        except authutils.AuthenticationError as e:
            logger.log("Unauthenticated DN='%s' acctgroup='%s'" %
                       (e.dn, e.acctgroup))
        except authutils.AuthorizationError as e:
            logger.log("Unauthorized DN='%s' acctgroup='%s'" %
                       (e.dn, e.acctgroup))


if __name__ == '__main__':
    """Entry point for krbrefresh cron job.
    """
    # Quick dirty hack that needs fixing
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test':
            test()
        elif sys.argv[1] == '--refresh-proxies':
            if len(sys.argv) >= 3:
                refresh_proxies(sys.argv[2])
            else:
                refresh_proxies()
            copy_user_krb5_caches()
