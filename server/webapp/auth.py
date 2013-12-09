#!/usr/bin/env python

################################################################################
# Project:
#   JobSub
#
# Author:
#   Parag Mhashilkar
#
# Description:
#   This module implements the JobSub webapp authN/authZ functionailty.
#   Some code and functionality is take from CDFCAF
#
# TODO:
#   The code still has lot of hardcoded path and makes several assumptions.
#   This needs to be cleaned up.
#
################################################################################


import os
import sys
import re
from distutils import spawn
import cherrypy
import logger
import subprocessSupport

class AuthenticationError(Exception):
    def __init__(self, dn, acctgroup=''):
       self.dn = dn
       self.acctgroup = acctgroup
       Exception.__init__(self, "Error authenticating DN='%s' for AcctGroup='%s'" % (self.dn, self.acctgroup))


class AuthorizationError(Exception):
    def __init__(self, dn, acctgroup=''):
       self.dn = dn
       self.acctgroup = acctgroup
       Exception.__init__(self, "Error authorizing DN='%s' for AcctGroup='%s'" % (self.dn, self.acctgroup))


class Krb5Ticket:

    def __init__(self, keytab, krb5cc, principal):
        self.keytab = keytab
        self.krb5cc = krb5cc
        self.principal = principal
        self.createLifetimeHours = 37
        self.renewableLifetimeHours = 72


    def create(self):
        kinit_exe = spawn.find_executable("kinit")
        if not kinit_exe:
            raise Exception("Unable to find command 'kinit' in the PATH.\nSTDERR:\n%s"%klist_err)

        cmd = '%s -F -t %s -l %ih -r %ih -c %s %s' % (kinit_exe, self.keytab,
                                                      self.createLifetimeHours,
                                                      self.renewableLifetimeHours,
                                                      self.krb5cc, self.principal)
        kinit_out, kinit_err = subprocessSupport.iexe_cmd(cmd)
        if kinit_err:
            raise Exception("createKrbCache error: %s" % kinit_err)


def krb5cc_to_vomsproxy(acctgroup, krb5cc,
                        proxy_fname='/tmp/x509up_u%s'%os.getuid()):
    # First convert the krb5cc to regular x509 credentials
    krb5cc_to_x509(krb5cc, x509_fname=proxy_fname)

    voms_proxy_init_exe = spawn.find_executable("voms-proxy-init")
    if not voms_proxy_init_exe:
        raise Exception("Unable to find command 'voms-proxy-init' in the PATH.\nSTDERR:\n%s"%klist_err)
    voms_group = 'fermilab:/fermilab/%s' % acctgroup
    cmd = "%s -noregen -valid 168:0 -bits 1024 -voms %s" % (voms_proxy_init_exe,
                                                            voms_group)
    cmd_env = {'X509_USER_PROXY': proxy_fname}
    cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd, child_env=cmd_env)


def krb5cc_to_x509(krb5cc, x509_fname='/tmp/x509up_u%s'%os.getuid()):
    kx509_exe = spawn.find_executable("kx509")
    if not kx509_exe:
        raise Exception("Unable to find command 'kx509' in the PATH.\nSTDERR:\n%s"%klist_err)

    cmd = '%s -o %s' % (kx509_exe, x509_fname)
    cmd_env = {'KRB5CCNAME': krb5cc}
    klist_out, klist_err = subprocessSupport.iexe_cmd(cmd, child_env=cmd_env)


def kadmin_password():
    passwd_file = os.environ.get('KADMIN_PASSWD_FILE')
    try:
        fd = open(passwd_file, 'r')
        password = ''.join(fd.readlines()).strip()
    except:
        print "ERROR: Reading kadmin password from %s" % passwd_file
        raise

    fd.close()
    return password


def add_principal(principal, keytab_fname):
    kadmin_command("addprinc -pw %s %s" % (kadmin_password(), principal))
    kadmin_command("ktadd -k %s %s" % (keytab_fname, principal))


def kadmin_command(command):
    cmd =  "kadmin -p fifegrid/batch/fifebatch1.fnal.gov@FNAL.GOV " \
           " -q \""+command+"\" -k -t fifegrid.keytab"


    cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd, child_env=cmd_env)
    if cmd_err:
        print "Error output from command: %s\n%s" % (cmd, cmd_err)
        return 1
    return 0


def authenticate(dn):
    # For now assume kerberos DN only
    KCA_DN_PATTERN = '^/DC=gov/DC=fnal/O=Fermilab/OU=People/CN.*/CN=UID:(.*$)'

    username = re.findall(KCA_DN_PATTERN, dn)
    if not (len(username) == 1 and username[0] != ''):
        raise AuthenticationError(dn)

    return username[0]

def authorize(dn, username, acctgroup):
    creds_dir = os.environ.get('JOBSUB_CREDENTIALS_DIR')

    try:
        principal = '%s/batch/fifegrid@FNAL.GOV' % username
        real_cache_fname = "%s/%s/krb5cc_%s" % (creds_dir, acctgroup, username)
        old_cache_fname = "%s/%s/old_krb5cc_%s" % (creds_dir, acctgroup, username)
        new_cache_fname = "%s/%s/new_krb5cc_%s" % (creds_dir, acctgroup, username)
        keytab_fname = "%s/%s/%s.keytab" % (creds_dir, acctgroup, username)
        x509_cache_fname = "%s/%s/x509cc_%s"%(creds_dir, acctgroup, username)

        # First create a keytab file for the user if it does not exists
        if not os.path.isfile(keytab_fname):
            add_principal(principal, keytab_fname)

        krb5_ticket = Krb5Ticket(keytab_fname, new_cache_fname, principal)
        krb5_ticket.create()

        # Rename is atomic and silently overwrites destination
        os.rename(real_cache_fname, old_cache_fname)
        os.rename(new_cache_fname, real_cache_fname)
        try:
            os.unlink(old_cache_fname)
        except:
            # Ignore file removal errors
            pass

        krb5cc_to_vomsproxy(acctgroup, real_cache_fname,
                            proxy_fname=x509_cache_fname)
        return x509_cache_fname
    except:
        raise AuthorizationError(dn, acctgroup)


def create_voms_proxy(dn, acctgroup):
    username = authenticate(dn)
    voms_proxy = authorize(dn, username, acctgroup)
    return voms_proxy


def refresh_proxies(access_map={}):
    # access_map is a dict of list. Outermost dict is keyed on username.
    access_map = {
        'boyd': ['minverva', 'nova', 'mu2e', 'minos'],
        'dbox': ['minverva', 'nova', 'mu2e', 'minos'],
        'parag': ['minverva', 'nova', 'mu2e', 'minos'],
    }

    for username in access_map:
        for acctgroup in access_map[username]:
            authorize('DN UNKNOWN DURING REFRESH', username, acctgroup)


def _check_auth(dn, acctgroup):
    return create_voms_proxy(dn, acctgroup)


def check_auth(func):
    def check_auth_wrapper(self, acctgroup, *args, **kwargs):
        dn = cherrypy.request.headers.get('Auth-User')
        if dn and acctgroup:
            logger.log('DN: %s, acctgroup: %s' % (dn, acctgroup))
            if _check_auth(dn, acctgroup):
                return func(self, acctgroup, *args, **kwargs)
            else:
                # return error for failed auth
                err = 'User authorization has failed'
                logger.log(err)
                rc = {'err': err}
        else:
            # return error for no subject_dn and acct group
            err = 'User has not supplied subject DN and/or accounting group'
            logger.log(err)
            rc = {'err': err}
        return rc

    return check_auth_wrapper


def test():
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
           print "Unauthenticated DN='%s' acctgroup='%s'" % (e.dn, e.acctgroup)
       except AuthorizationError, e:
           print "Unauthorized DN='%s' acctgroup='%s'" % (e.dn, e.acctgroup)



"""
##### PREVIOUS CODE
from subprocess import Popen, PIPE
import logger

def execute_gums_command(subject_dn, accountinggroup):
    command = '/usr/bin/gums-host|mapUser|-g|https://gums.fnal.gov:8443/gums/services/GUMSXACMLAuthorizationServicePort|%s|-f|/fermilab/%s' % (subject_dn, accountinggroup)
    command = command.split('|')
    logger.log('gums command: %s' % command)
    pp = Popen(command, stdout=PIPE, stderr=PIPE)
    result = {
        'out': pp.stdout.readlines(),
        'err': pp.stderr.readlines()
    }
    logger.log('gums command result: %s' % str(result))
    return result


def _check_auth(subject_dn, accountinggroup):
    result = execute_gums_command(subject_dn, accountinggroup)
    if result['out'][0].startswith('null') or len(result['err']) > 0:
        return False
    else:
        return True


def check_auth(func):
    def check_auth_wrapper(self, acctgroup, *args, **kwargs):
        subject_dn = cherrypy.request.headers.get('Auth-User')
        if subject_dn is not None and acctgroup is not None:
            logger.log('subject_dn: %s, acctgroup: %s' % (subject_dn, acctgroup))
            if _check_auth(subject_dn, acctgroup):
                return func(self, acctgroup, *args, **kwargs)
            else:
                # return error for failed auth
                err = 'User authorization has failed'
                logger.log(err)
                rc = {'err': err}
        else:
            # return error for no subject_dn and acct group
            err = 'User has not supplied subject dn and/or accounting group'
            logger.log(err)
            rc = {'err': err}
        return rc

    return check_auth_wrapper

"""


if __name__ == '__main__':
    # Quick dirty hack that needs fixing
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test':
            test()
        elif sys.argv[1] == '--refresh-proxies':
            refresh_proxies()
