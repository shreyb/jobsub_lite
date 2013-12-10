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
            raise Exception("Unable to find command 'kinit' in the PATH.")

        cmd = '%s -F -k -t %s -l %ih -r %ih -c %s %s' % (kinit_exe, self.keytab,
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
        raise Exception("Unable to find command 'voms-proxy-init' in the PATH.")
    voms_group = 'fermilab:/fermilab/%s' % acctgroup
    cmd = "%s -noregen -valid 168:0 -bits 1024 -voms %s" % (voms_proxy_init_exe, voms_group)
    cmd_env = {'X509_USER_PROXY': proxy_fname}
    cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd, child_env=cmd_env)


def krb5cc_to_x509(krb5cc, x509_fname='/tmp/x509up_u%s'%os.getuid()):
    kx509_exe = spawn.find_executable("kx509")
    if not kx509_exe:
        kx509_exe = '/usr/krb5/bin/kx509'
    #if not os.path.exists(kx509_exe):
    #    raise Exception("Unable to find command 'kx509' in the PATH.")

    cmd = '%s -o %s' % (kx509_exe, x509_fname)
    cmd_env = {'KRB5CCNAME': krb5cc}
    klist_out, klist_err = subprocessSupport.iexe_cmd(cmd, child_env=cmd_env)


def kadmin_password():
    passwd_file = os.environ.get('KADMIN_PASSWD_FILE')
    logger.log('Using KADMIN PASSWORD FILE: %s' % passwd_file)
    try:
        fd = open(passwd_file, 'r')
        password = ''.join(fd.readlines()).strip()
    except:
        logger.log("ERROR: Reading kadmin password from %s" % passwd_file)
        raise

    fd.close()
    return password


def add_principal(principal, keytab_fname):
    logger.log('Adding principal %s to the krb5 database' % principal)
    kadmin_command("addprinc -pw %s %s" % (kadmin_password(), principal))
    logger.log('Adding keytab %s' % keytab_fname)
    kadmin_command("ktadd -k %s %s" % (keytab_fname, principal))


def kadmin_command(command):
    creds_base_dir = os.environ.get('JOBSUB_CREDENTIALS_DIR')
    fifegrid_keytab = os.path.join(creds_base_dir, 'fifegrid.keytab')
    cmd = "kadmin -p fifegrid/batch/fifebatch1.fnal.gov@FNAL.GOV " \
           " -q \""+command+"\" -k -t %s" % fifegrid_keytab

    logger.log('Executing: %s' % cmd)
    cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd)
    if cmd_err:
        logger.log("Error output from command: %s\n%s" % (cmd, cmd_err))
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
    creds_base_dir = os.environ.get('JOBSUB_CREDENTIALS_DIR')
    creds_dir = os.path.join(creds_base_dir, acctgroup)
    logger.log('Using credentials dir: %s' % creds_dir)
    try:
        principal = '%s/batch/fifegrid@FNAL.GOV' % username
        if not os.path.isdir(creds_dir):
            os.makedirs(creds_dir, 0700)
        real_cache_fname = os.path.join(creds_dir, 'krb5cc_%s'%username)
        old_cache_fname = os.path.join(creds_dir, 'old_krb5cc_%s'%username)
        new_cache_fname = os.path.join(creds_dir, 'new_krb5cc_%s'%username)
        keytab_fname = os.path.join(creds_dir, '%s.keytab'%username)
        x509_cache_fname = os.path.join(creds_dir, 'x509cc_%s'%username)

        # First create a keytab file for the user if it does not exists
        if not os.path.isfile(keytab_fname):
            logger.log('Using keytab %s to add principal %s ...' % (keytab_fname, principal))
            add_principal(principal, keytab_fname)
            logger.log('Using keytab %s to add principal %s ... DONE' % (keytab_fname, principal))

        logger.log('Creating krb5 ticket ...')
        krb5_ticket = Krb5Ticket(keytab_fname, new_cache_fname, principal)
        krb5_ticket.create()
        logger.log('Creating krb5 ticket ... DONE')

        # Rename is atomic and silently overwrites destination
        if os.path.exists(real_cache_fname):
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
        import traceback
        logger.log('EXCEPTION OCCURED IN AUTHORIZATION')
        logger.log(traceback.format_exc())
        raise AuthorizationError(dn, acctgroup)


def create_voms_proxy(dn, acctgroup):
    logger.log('Authenticating DN: %s' % dn)
    username = authenticate(dn)
    logger.log('Authorizing user: %s' % username)
    voms_proxy = authorize(dn, username, acctgroup)
    logger.log('User authorized. Voms proxy file: %s' % voms_proxy)
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
            try:
                if _check_auth(dn, acctgroup):
                    return func(self, acctgroup, *args, **kwargs)
                else:
                    # return error for failed auth
                    err = 'User authorization has failed'
                    logger.log(err)
                    rc = {'err': err}
            except:
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
           logger.log("Unauthenticated DN='%s' acctgroup='%s'" % (e.dn, e.acctgroup))
       except AuthorizationError, e:
           logger.log("Unauthorized DN='%s' acctgroup='%s'" % (e.dn, e.acctgroup))


if __name__ == '__main__':
    # Quick dirty hack that needs fixing
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test':
            test()
        elif sys.argv[1] == '--refresh-proxies':
            refresh_proxies()
