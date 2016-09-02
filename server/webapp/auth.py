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
import re
import time
import traceback
import cherrypy
import logger
import logging
import jobsub
import subprocessSupport

from functools import wraps, partial
from distutils import spawn
from tempfile import NamedTemporaryFile
from JobsubConfigParser import JobsubConfigParser


class AuthenticationError(Exception):
    """Authentication Exception.  I do not recognize you as who you 
       claim you are.

       Args:
           dn       : DN of certificate you are presenting
           acctgroup: Accounting group or experiment you are trying 
           to authenticate to

    """

    def __init__(self, dn, acctgroup=''):
        cherrypy.response.status = 401
        self.dn = dn
        self.acctgroup = acctgroup
        fmt = "Error authenticating DN='%s' for AcctGroup='%s'"
        Exception.__init__(self, fmt % (self.dn, self.acctgroup))


class AuthorizationError(Exception):
    """Authorization Exception.  You are not authorized to perform desired 
       action as member of acctgroup

       Args:
           dn       : DN of certificate you are presenting
           acctgroup: Accounting group or experiment you are trying to 
           authorize from

    """

    def __init__(self, dn, acctgroup=''):
        cherrypy.response.status = 401
        self.dn = dn
        self.acctgroup = acctgroup
        fmt = "Error authorizing DN='%s' for AcctGroup='%s'"
        Exception.__init__(self, fmt % (self.dn, self.acctgroup))


class OtherAuthError(Exception):
    """General Authorization Error

       Args:
           errmsg: error message, if known

    """

    def __init__(self,
                 errmsg=''.join(["Authentication Error, ",
                                 "please open a service desk ticket", ])):
        cherrypy.response.status = 401
        Exception.__init__(self, errmsg)


class Krb5Ticket(object):
    """ Kerberos 5 ticket

        Args:
            keytab   : kerberos5 keytab
            krb5cc   : kerberos5 credential cache 
            principal: kerberos principal subject name
    """

    def __init__(self, keytab, krb5cc, principal):
        cherrypy.request.keytab = keytab
        cherrypy.request.krb5cc = krb5cc
        cherrypy.request.principal = principal
        self.createLifetimeHours = 37
        self.renewableLifetimeHours = 168

    def create(self):
        """create the ticket cache"""
        try:
            kinit_exe = spawn.find_executable("kinit")
        except:
            raise OtherAuthError("Unable to find command 'kinit' in the PATH.")

        cmd = '%s -F -k -t %s -l %ih -r %ih -c %s %s' %\
            (kinit_exe, cherrypy.request.keytab,
             self.createLifetimeHours,
             self.renewableLifetimeHours,
             cherrypy.request.krb5cc,
             cherrypy.request.principal)
        logger.log(cmd)
        try:
            kinit_out, kinit_err = subprocessSupport.iexe_cmd(cmd)
        except:
            logger.log('removing file %s' % cherrypy.request.krb5cc)
            os.remove(cherrypy.request.krb5cc)
            raise OtherAuthError("%s failed:  %s" % (cmd, sys.exc_info()[1]))


def get_voms(acctgroup):
    """get the VOMS string for voms-proxy-init from jobsub.ini config file
    """
    voms_group = 'fermilab:/fermilab/%s' % acctgroup
    p = JobsubConfigParser()
    if p.has_section(acctgroup):
        if p.has_option(acctgroup, 'voms'):
            voms_group = p.get(acctgroup, 'voms')
    else:
        raise jobsub.AcctGroupNotConfiguredError(acctgroup)
    return voms_group


def krbrefresh_query_fmt():
    """get format string for krbrefresh command from jobsub.ini config file
    """
    query_fmt = ''.join([""" -format "%s," accountinggroup -format "%s," """,
                         """x509userproxysubject -format "%s" x509userproxy""",
                         """ -format "\n" ClusterId -constraint """,
                         """'JobUniverse=!=7&&x509userproxysubject""",
                         """=!=UNDEFINED' """,
                         ])
    p = JobsubConfigParser()
    if p.has_section('default'):
        qf = p.get('default', 'krbrefresh_query_format')
        if qf:
            query_fmt = qf
    logger.log('query_fmt=%s' % query_fmt)
    return query_fmt


def get_voms_attrs(acctgroup, acctrole=None):
    """Add voms ROLE to fqan if needed 
    """
    fqan = get_voms(acctgroup)
    if acctrole:
        fqan = '%s/Role=%s' % (fqan, acctrole)
    return fqan


def get_voms_fqan(acctgroup, acctrole=None):
    """return the fqan from the VOMS string
    """
    attrs = get_voms_attrs(acctgroup, acctrole=acctrole).split(':')
    return attrs[-1]


def x509pair_to_vomsproxy(cert, key, proxy_fname, acctgroup, acctrole=None):
    """generate a VOMS proxy from x509 cert/key pair
    """
    tmp_proxy_fname = mk_temp_fname(proxy_fname)
    logger.log("tmp_proxy_fname=%s" % tmp_proxy_fname)
    voms_proxy_init_exe = spawn.find_executable("voms-proxy-init")
    if not voms_proxy_init_exe:
        err = "Unable to find command 'voms-proxy-init' in the PATH."
        logger.log(err, severity=logging.ERROR)
        logger.log(err, severity=logging.ERROR, logfile='error')
        raise Exception(err)

    # Any exception raised will result in Authorization Error by the caller
    try:
        voms_attrs = get_voms_attrs(acctgroup, acctrole)
    except jobsub.AcctGroupNotConfiguredError, e:
        logger.log("%s" % e, severity=logging.ERROR)
        logger.log("%s" % e, severity=logging.ERROR, logfile='error')
        raise

    p = JobsubConfigParser()
    voms_proxy_lifetime = p.get('default', 'voms_proxy_lifetime')
    if not voms_proxy_lifetime:
        voms_proxy_lifetime = '168:0'
    cmd = "%s -noregen -rfc -ignorewarn -valid %s -bits 1024 -voms %s -out\
            %s -cert %s -key %s" %\
        (voms_proxy_init_exe, voms_proxy_lifetime,
         voms_attrs, tmp_proxy_fname, cert, key)
    logger.log(cmd)
    make_proxy_from_cmd(cmd, proxy_fname, tmp_proxy_fname, role=acctrole)


def krb5cc_to_vomsproxy(krb5cc, proxy_fname, acctgroup, acctrole=None):
    """Generate a VOMS proxy from a Kerberos ticket cache
    """
    new_proxy_fname = mk_temp_fname(proxy_fname)
    krb5cc_to_x509(krb5cc, x509_fname=new_proxy_fname)

    voms_proxy_init_exe = spawn.find_executable("voms-proxy-init")
    if not voms_proxy_init_exe:
        raise Exception(
            "Unable to find command 'voms-proxy-init' in the PATH.")

    # Any exception raised will result in Authorization Error by the caller
    try:
        voms_attrs = get_voms_attrs(acctgroup, acctrole)
    except jobsub.AcctGroupNotConfiguredError, e:
        os.remove(new_proxy_fname)
        logger.log("%s" % e, severity=logging.ERROR)
        logger.log("%s" % e, severity=logging.ERROR, logfile='error')
        raise

    p = JobsubConfigParser()
    voms_proxy_lifetime = p.get('default', 'voms_proxy_lifetime')
    if not voms_proxy_lifetime:
        voms_proxy_lifetime = '168:0'
    cmd = "%s -noregen -rfc -ignorewarn -valid %s -bits 1024 -voms %s" %\
        (voms_proxy_init_exe, voms_proxy_lifetime, voms_attrs)
    cmd_env = {'X509_USER_PROXY': new_proxy_fname}
    logger.log(cmd)
    make_proxy_from_cmd(cmd, proxy_fname, new_proxy_fname,
                        role=acctrole, env_dict=cmd_env)


def mk_temp_fname(fname):
    """Generate a temporary file name to store credentials to
       avoid race conditions
    """
    tmp_file = NamedTemporaryFile(prefix="%s_" % fname, delete=False)
    tmp_fname = tmp_file.name
    tmp_file.close()
    return tmp_fname


def make_proxy_from_cmd(cmd, proxy_fname, tmp_proxy_fname,
                        role=None, env_dict=None):
    """Do the actual generation of a VOMS proxy given an input command 'cmd'
    """

    logger.log('cmd=%s proxy_fname=%s tmp_proxy_fname=%s role=%s ' %
               (cmd, proxy_fname, tmp_proxy_fname, role))
    voms_proxy_info_exe = spawn.find_executable("voms-proxy-info")
    if not voms_proxy_info_exe:
        raise OtherAuthError(
            "Unable to find command 'voms-proxy-init' in the PATH.")

    try:
        cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd, child_env=env_dict)
    except:
        # Catch and ignore warnings
        proxy_created_pattern = 'Creating proxy  Done'
        proxy_pattern_2 = 'Warning: your certificate and proxy will expire'
        tb = traceback.format_exc()
        if len(re.findall(proxy_created_pattern, tb)):
            logger.log('Proxy was created. Ignoring warnings.')
            logger.log('Output from running voms-proxy-init:\n%s' % tb)
        elif len(re.findall(proxy_pattern_2, tb)):
            logger.log('Proxy was created. Ignoring warnings.')
            logger.log('Output from running voms-proxy-init:\n%s' % tb)
        else:
            logger.log('failed tb=%s' % tb, severity=logging.ERROR)
            logger.log('failed tb=%s' %
                       tb, severity=logging.ERROR, logfile='error')
            logger.log('removing %s' % tmp_proxy_fname)

            # Anything else we should just raise
            os.remove(tmp_proxy_fname)
            raise

    cmd = "%s -all -file %s " % (voms_proxy_info_exe, tmp_proxy_fname)
    logger.log(cmd)
    try:
        cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd)
        if role:
            role_pattern = "/Role=%s/Capability" % (role)
            if (role_pattern in cmd_out) and ('VO' in cmd_out):
                logger.log('found role %s , authenticated successfully' %
                           (role_pattern))
                os.rename(tmp_proxy_fname, proxy_fname)
            else:
                logger.log('failed to find %s in %s' % (role_pattern, cmd_out))
                t1 = role_pattern in cmd_out
                t2 = 'VO' in cmd_out
                logger.log('test (%s in cmd_out)=%s test(VO in cmd_out)=%s' %
                           (role_pattern, t1, t2))
                os.remove(tmp_proxy_fname)
                err = "unable to authenticate with role='%s'. Typo?" % role
                logger.log(err, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')
                raise OtherAuthError(err)

        else:
            if ('VO' in cmd_out):
                os.rename(tmp_proxy_fname, proxy_fname)
            else:
                os.remove(tmp_proxy_fname)
                err = "result:%s:%s does not appear to contain " %\
                      (cmd_out, cmd_err)
                err += "valid VO information. Failed to authenticate"
                logger.log(err, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')
                raise OtherAuthError(
                    ''.join(["Your certificate is not valid. ",
                             "Please contact the service desk"]))
    except:
        err = "%s" % sys.exc_info()[1]
        logger.log(err, severity=logging.ERROR)
        logger.log(err, severity=logging.ERROR, logfile='error')
        raise OtherAuthError(err)
    finally:
        if os.path.exists(tmp_proxy_fname):
            os.remove(tmp_proxy_fname)


def krb5cc_to_x509(krb5cc, x509_fname='/tmp/x509up_u%s' % os.getuid()):
    """Generate X509 proxy from kerberos cache
    """
    kx509_exe = spawn.find_executable("kx509")
    if not kx509_exe:
        kx509_exe = '/usr/krb5/bin/kx509'
    # if not os.path.exists(kx509_exe):
    #    raise Exception("Unable to find command 'kx509' in the PATH.")

    cmd = '%s -o %s' % (kx509_exe, x509_fname)
    cmd_env = {'KRB5CCNAME': krb5cc}
    logger.log(cmd)
    try:
        klist_out, klist_err = subprocessSupport.iexe_cmd(
            cmd, child_env=cmd_env)
    except:
        err = "%s" % sys.exc_info()[1]
        logger.log(err, severity=logging.ERROR)
        logger.log(err, severity=logging.ERROR, logfile='error')
        if os.path.exists(x509_fname):
            os.remove(x509_fname)
        raise OtherAuthError(err)


def kadmin_password():
    """Locate kadmin password file
    """
    passwd_file = os.environ.get('KADMIN_PASSWD_FILE')
    logger.log('Using KADMIN PASSWORD FILE: %s' % passwd_file)
    try:
        fd = open(passwd_file, 'r')
        password = ''.join(fd.readlines()).strip()
    except:
        err = "error reading kadmin password from %s" % passwd_file
        logger.log(err, severity=logging.ERROR)
        logger.log(err, severity=logging.ERROR, logfile='error')
        raise

    fd.close()
    return password


def add_principal(principal, keytab_fname):
    """ add kerberos principal to kerberos database
    """
    logger.log('Adding principal %s to the krb5 database' % principal)
    kadmin_command("addprinc -pw %s %s" % (kadmin_password(), principal))
    logger.log('Adding keytab %s' % keytab_fname)
    kadmin_command("ktadd -k %s %s" % (keytab_fname, principal))


def kadmin_command(command):
    """execute kadmin command on input string 'command'
    """
    creds_base_dir = os.environ.get('JOBSUB_CREDENTIALS_DIR')
    fifegrid_keytab = os.path.join(creds_base_dir, 'fifegrid.keytab')
    cmd = "kadmin -p fifegrid/batch/fifebatch1.fnal.gov@FNAL.GOV " \
        " -q \"" + command + "\" -k -t %s" % fifegrid_keytab

    logger.log('Executing: %s' % cmd)
    cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd)
    if cmd_err:
        stat = "Error output from command: %s\n%s" % (cmd, cmd_err)
        logger.log(stat, severity=logging.ERROR)
        logger.log(stat, severity=logging.ERROR, logfile='error')
        return 1
    return 0






def authenticate(dn, acctgroup, acctrole):
    """Check which authentication method used by acctgroup
       and try that method
    """
    methods = jobsub.get_authentication_methods(acctgroup)
    logger.log("Authentication method precedence: %s" % methods)
    for method in methods:
        cherrypy.response.status = 200
        logger.log("Authenticating using method: %s" % method)
        try:
            if method.lower() in ['gums' ,'myproxy']:
                try:
                    import auth_gums
                    return auth_gums.authenticate(dn, acctgroup, acctrole)
                except Exception, e:
                    logger.log('failed %s'%e)
            elif method.lower() == 'kca-dn':
                try:
                    import auth_kca
                    return auth_kca.authenticate(dn)
                except Exception, e:
                    logger.log('failed %s'%e)
            else:
                logger.log("Unknown authenticate method: %s" % method)
        except:
            logger.log("Failed to authenticate using method: %s" % method)

    err = "Failed to authenticate dn '%s' for group '%s' with role '%s' using known authentication methods" %\
        (dn, acctgroup, acctrole)
    logger.log(err, severity=logging.ERROR)
    logger.log(err, severity=logging.ERROR, logfile='error')
    raise AuthenticationError(dn, acctgroup)


def clean_proxy_dn(dn):
    """Strip off proxy-of-proxy info to the the 'root' proxy
    """
    cn_pat = re.compile('/CN=[0-9]+')
    for p in cn_pat.findall(dn):
        dn = dn.replace(p, '')
    p_pat = re.compile('/CN=proxy')
    for p in p_pat.findall(dn):
        dn = dn.replace(p, '')
    return dn



def x509_proxy_fname(username, acctgroup, acctrole=None):
    """generate file name to store x509 proxy 
    """
    #creds_base_dir = os.environ.get('JOBSUB_CREDENTIALS_DIR')
    jobsubConfig = jobsub.JobsubConfig()
    proxies_base_dir = jobsubConfig.proxiesDir
    creds_dir = os.path.join(proxies_base_dir, acctgroup)
    if not os.path.isdir(creds_dir):
        os.makedirs(creds_dir, 0755)
    if acctrole:
        x509_cache_fname = os.path.join(creds_dir,
                                        'x509cc_%s_%s' % (username, acctrole))
    else:
        x509_cache_fname = os.path.join(creds_dir, 'x509cc_%s' % username)
    logger.log('Using x509_proxy_name=%s' % x509_cache_fname)
    return x509_cache_fname


def authorize(dn, username, acctgroup, acctrole=None, age_limit=3600):
    """Decide authorization method for acctgroup and do it
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
                    return auth_kca.authorize_kca(dn, username,
                                     acctgroup, acctrole, age_limit)
                except Exception, e:
                    logger.log('authoriziation failed, %s'%e)

            elif method.lower() == 'myproxy':
                try:
                    import auth_myproxy
                    return auth_myproxy.authorize(dn, username,
                                                  acctgroup, acctrole,
                                                  age_limit)
                except Exception, e:
                    logger.log('myproxy authoriziation failed, %s'%e)

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
    raise AuthenticationError(dn, acctgroup)


# for stress testing,add as second parameter to needs_refresh()
# these times are in seconds, not hours so refresh every 24 seconds for daily
# REFRESH_DAILY=24
# REFRESH_EVERY_4_HOURS=4



def refresh_krb5cc(username):
    """Generate new kerberos cache for 'username'
    """
    try:
        creds_base_dir = os.environ.get('JOBSUB_CREDENTIALS_DIR')
        jobsubConfig = jobsub.JobsubConfig()
        principal = '%s/batch/fifegrid@FNAL.GOV' % username
        krb5cc_dir = jobsubConfig.krb5ccDir
        keytab_fname = os.path.join(creds_base_dir, '%s.keytab' % username)
        real_cache_fname = os.path.join(krb5cc_dir, 'krb5cc_%s' % username)
        new_cache_file = NamedTemporaryFile(
            prefix="%s_" % real_cache_fname, delete=False)
        new_cache_fname = new_cache_file.name
        new_cache_file.close()
        logger.log("new_cache_fname=%s" % new_cache_fname)
        logger.log('Creating krb5 ticket ...')
        krb5_ticket = Krb5Ticket(keytab_fname, new_cache_fname, principal)
        krb5_ticket.create()
        logger.log('Creating krb5 ticket ... DONE')
        os.rename(new_cache_fname, real_cache_fname)
        return real_cache_fname
    except Exception, e:
        logger.log(str(e), severity=logging.ERROR)
        logger.log(str(e), severity=logging.ERROR, logfile='error')
        raise
    finally:
        if os.path.exists(new_cache_fname):
            os.remove(new_cache_fname)
            logger.log("cleanup:rm %s" % new_cache_fname)

    return None

def is_valid_cache(cache_name):
    """Check if 'cache_name' is valid
    """
    # this always returns False after ownership change of cache_name from 'rexbatch' to its actual uid
    # i.e. klist -s executed as 'rexbatch' silently returns 1 in this case with no error output.
    # What we missed is that a copy_file_as_user(cache_name, /fife/local/scratch/uploads/...cache_name, username)
    # is needed after krbrefresh to keep the jobs krb5 cache updated
    #
    klist_exe = spawn.find_executable("klist")
    cmd = "%s -s -c %s" % (klist_exe, cache_name)
    try:
        logger.log(cmd)
        cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd)
        logger.log("%s is still valid" % cache_name)
        return True
    except:
        err = "%s is expired,invalid, or does not exist" % cache_name
        logger.log(err, severity=logging.ERROR)
        logger.log(err, severity=logging.ERROR, logfile='error')
        return False


def create_voms_proxy(dn, acctgroup, role):
    """create a VOMS proxy:
          first authenticate() 
          then authorize()
    """
    logger.log('create_voms_proxy: Authenticating DN: %s' % dn)
    username = authenticate(dn, acctgroup, role)
    logger.log('create_voms_proxy: Authorizing user: %s acctgroup: %s role: %s' % (
        username, acctgroup, role))
    voms_proxy = authorize(dn, username, acctgroup, role)
    logger.log('User authorized. Voms proxy file: %s' % voms_proxy)
    return (username, voms_proxy)


def refresh_proxies(agelimit=3600):
    """refresh proxies for all jobs in queue older than 'agelimit'
       called from cron
    """
    cmd = spawn.find_executable('condor_q')
    if not cmd:
        err = 'Unable to find condor_q in the PATH'
        logger.log(err, severity=logging.ERROR)
        logger.log(err, severity=logging.ERROR, logfile='error')
        raise Exception(err)
    cmd += krbrefresh_query_fmt()
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


def needs_refresh(filepath, agelimit=3600):
    """Check if filepath is older than agelimit. If yes,
       filepath needs refreshing
    """
    logger.log("%s %s" % (filepath, agelimit))
    if not os.path.exists(filepath):
        logger.log("%s does not exist, need to refresh" % filepath)
        return True
    if agelimit == sys.maxint:
        return False
    rslt = False
    agelimit = int(agelimit)
    age = sys.maxint
    try:
        st = os.stat(filepath)
        age = (time.time() - st.st_mtime)
    except:
        err = '%s' % sys.exc_info()[1]
        logger.log(err)
    logger.log('age of %s is %s, compare to agelimit=%s' %
               (filepath, age, agelimit))
    if age > agelimit:
        rslt = True
    return rslt


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
            create_voms_proxy(dns[group], group)
        except AuthenticationError, e:
            logger.log("Unauthenticated DN='%s' acctgroup='%s'" %
                       (e.dn, e.acctgroup))
        except AuthorizationError, e:
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
