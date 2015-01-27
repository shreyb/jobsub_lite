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
import traceback
import cherrypy
import logger
import jobsub
import subprocessSupport

from distutils import spawn
from util import needs_refresh
from tempfile import NamedTemporaryFile
from JobsubConfigParser import JobsubConfigParser


class AuthenticationError(Exception):
    def __init__(self, dn, acctgroup=''):
        cherrypy.response.status = 401
        self.dn = dn
        self.acctgroup = acctgroup
        Exception.__init__(self, "Error authenticating DN='%s' for AcctGroup='%s'" % (self.dn, self.acctgroup))


class AuthorizationError(Exception):
    def __init__(self, dn, acctgroup=''):
        cherrypy.response.status = 401
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
        logger.log(cmd)
        try:
            kinit_out, kinit_err = subprocessSupport.iexe_cmd(cmd)
        except:
            logger.log('removing file %s'%self.krb5cc)
            os.remove(self.krb5cc)
            raise 


def get_voms(acctgroup):
    voms_group = 'fermilab:/fermilab/%s' % acctgroup
    p = JobsubConfigParser()
    if p.has_section(acctgroup):
        if p.has_option(acctgroup, 'voms'):
            voms_group = p.get(acctgroup, 'voms')
    else:
        raise jobsub.AcctGroupNotConfiguredError(acctgroup)
    return voms_group


def get_voms_attrs(acctgroup, acctrole=None):
    fqan = get_voms(acctgroup)
    if acctrole:
        fqan = '%s/Role=%s' % (fqan, acctrole)
    return fqan


def get_voms_fqan(acctgroup, acctrole=None):
    attrs = get_voms_attrs(acctgroup, acctrole=acctrole).split(':')
    return attrs[-1]


def x509pair_to_vomsproxy(cert, key, proxy_fname, acctgroup, acctrole=None):
    # TODO: krb5cc_to_vomsproxy and x509pair_to_vomsproxy share lot of
    #       code. Extract common functionality to conert x509 to voms proxy

    tmp_proxy_file = NamedTemporaryFile(prefix="%s_"%proxy_fname, delete=False)
    tmp_proxy_fname = tmp_proxy_file.name
    tmp_proxy_file.close()
    logger.log("tmp_proxy_fname=%s"%tmp_proxy_fname)
    voms_proxy_init_exe = spawn.find_executable("voms-proxy-init")
    voms_proxy_info_exe = spawn.find_executable("voms-proxy-info")
    if not voms_proxy_init_exe:
        raise Exception("Unable to find command 'voms-proxy-init' in the PATH.")

    voms_proxy_init_exe = spawn.find_executable("voms-proxy-init")
    voms_proxy_info_exe = spawn.find_executable("voms-proxy-info")
    if not voms_proxy_init_exe:
        raise Exception("Unable to find command 'voms-proxy-init' in the PATH.")

    # Any exception raised will result in Authorization Error by the caller
    try:
        voms_attrs = get_voms_attrs(acctgroup, acctrole)
    except jobsub.AcctGroupNotConfiguredError, e: 
        logger.log("%s"%e) 
        raise

    cmd = "%s -noregen -rfc -ignorewarn -valid 168:0 -bits 1024 -voms %s -out %s -cert %s -key %s" % (voms_proxy_init_exe, voms_attrs, tmp_proxy_fname, cert, key)
    logger.log(cmd)

    try:
        cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd)
    except:
        # Catch and ignore warnings
        proxy_created_pattern = 'Creating proxy  Done'
        tb = traceback.format_exc()
        if len(re.findall(proxy_created_pattern, tb)):
            logger.log('Proxy was created. Ignoring warnings.')
            logger.log('Output from running voms-proxy-init:\n%s' % tb) 
        else:
            # Anything else we should just raise
            os.remove(tmp_proxy_fname)
            raise
    cmd = "%s -all -file %s | grep VO"%(voms_proxy_info_exe,tmp_proxy_fname)
    logger.log(cmd)
    ret_code = os.system(cmd)
    if ret_code == 0:
	os.rename(tmp_proxy_fname, proxy_fname)
    else:
        os.remove(tmp_proxy_fname)


def krb5cc_to_vomsproxy(krb5cc, proxy_fname, acctgroup, acctrole=None):
    # First convert the krb5cc to regular x509 credentials
    new_proxy_file = NamedTemporaryFile(prefix="%s_"%proxy_fname, delete=False)
    new_proxy_fname = new_proxy_file.name
    logger.log("new_proxy_fname=%s"%new_proxy_fname)
    new_proxy_file.close()
    krb5cc_to_x509(krb5cc, x509_fname=new_proxy_fname)

    voms_proxy_init_exe = spawn.find_executable("voms-proxy-init")
    voms_proxy_info_exe = spawn.find_executable("voms-proxy-info")
    if not voms_proxy_init_exe:
        raise Exception("Unable to find command 'voms-proxy-init' in the PATH.")

    # Any exception raised will result in Authorization Error by the caller
    try:
        voms_attrs = get_voms_attrs(acctgroup, acctrole)
    except jobsub.AcctGroupNotConfiguredError, e: 
        os.remove(new_proxy_fname)
        logger.log("%s"%e) 
        raise

    cmd = "%s -noregen -rfc -ignorewarn -valid 168:0 -bits 1024 -voms %s" % (voms_proxy_init_exe, voms_attrs)
    cmd_env = {'X509_USER_PROXY': new_proxy_fname}
    logger.log(cmd)
    try:
        cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd, child_env=cmd_env)
    except:
        # Catch and ignore warnings
        # warning_pattern = 'Warning: voms.fnal.gov:[0-9]*: The validity of this VOMS AC in your proxy is shortened to [0-9]* seconds!'
        proxy_created_pattern = 'Creating proxy  Done'
        tb = traceback.format_exc()
        if len(re.findall(proxy_created_pattern, tb)):
            logger.log('Proxy was created. Ignoring warnings.')
            logger.log('Output from running voms-proxy-init:\n%s' % tb) 
        else:
            # Anything else we should just raise
            raise
    cmd = "%s -all -file %s | grep VO"%(voms_proxy_info_exe,new_proxy_fname)
    logger.log(cmd)
    ret_code = os.system(cmd)
    if ret_code == 0:
	os.rename(new_proxy_fname,proxy_fname)
    else:
        os.remove(new_proxy_fname)


def krb5cc_to_x509(krb5cc, x509_fname='/tmp/x509up_u%s'%os.getuid()):
    kx509_exe = spawn.find_executable("kx509")
    if not kx509_exe:
        kx509_exe = '/usr/krb5/bin/kx509'
    #if not os.path.exists(kx509_exe):
    #    raise Exception("Unable to find command 'kx509' in the PATH.")

    cmd = '%s -o %s' % (kx509_exe, x509_fname)
    cmd_env = {'KRB5CCNAME': krb5cc}
    logger.log(cmd)
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


def authenticate_kca_dn(dn):
    KCA_DN_PATTERN_LIST=os.environ.get('KCA_DN_PATTERN_LIST')
    logger.log("dns patterns supported:%s "% KCA_DN_PATTERN_LIST )

    for pattern in KCA_DN_PATTERN_LIST.split(','):
    	username = re.findall(pattern, dn)
    	if len(username) >= 1 and username[0] != '':
		return username[0]

    raise AuthenticationError(dn)


def authenticate_gums(dn, acctgroup, acctrole):
    try:
        fqan = get_voms_fqan(acctgroup, acctrole)
        username = get_gums_mapping(dn, fqan)
        username = username.strip()
        logger.log("GUMS mapped dn '%s' fqan '%s' to '%s'" % (dn, fqan, username))
        return username
    except:
        logger.log("GUMS mapping for the dn '%s' fqan '%s' failed" % (dn, fqan), traceback=True)
    raise AuthenticationError(dn, acctgroup)


def authenticate(dn, acctgroup, acctrole):
    try:
        return authenticate_gums(dn, acctgroup, acctrole)
    except:
        logger.log("Failed to authenticate using GUMS. Checking for KCA DN based authentication")

    #raise AuthenticationError(dn, acctgroup)
    logger.log("Authenticating using KCA DN Pattern.")
    try:
        username = authenticate_kca_dn(dn)
        cherrypy.response.status = 200
        return username
    except:
        logger.log("Failed to authenticate using KCA DN Pattern.")

    logger.log("Failed to authenticate dn '%s' for group '%s' with role '%s' using known authentication methods." % (dn, acctgroup, acctrole))
    raise AuthenticationError(dn, acctgroup)


def get_gums_mapping(dn, fqan):
    exe = jobsub.get_jobsub_priv_exe()
    cmd = '%s getMappedUsername "%s" "%s"' % (exe, dn, fqan)
    err = ''
    logger.log(cmd)
    try:
        out, err = subprocessSupport.iexe_priv_cmd(cmd)
    except:
        logger.log('Error running command %s: %s' % (cmd, err))
        raise 
    return out


def x509_proxy_fname(username, acctgroup, acctrole=None):
    #creds_base_dir = os.environ.get('JOBSUB_CREDENTIALS_DIR')
    proxies_base_dir = jobsub.get_jobsub_proxies_dir()
    creds_dir = os.path.join(proxies_base_dir, acctgroup)
    if not os.path.isdir(creds_dir):
        os.makedirs(creds_dir, 0755)
    if acctrole:
        x509_cache_fname = os.path.join(creds_dir,
                                        'x509cc_%s_%s'%(username,acctrole))
    else:
        x509_cache_fname = os.path.join(creds_dir, 'x509cc_%s'%username)
    logger.log('Using x509_proxy_name=%s'%x509_cache_fname)
    return x509_cache_fname

#for stress testing,add as second parameter to needs_refresh()
# these times are in seconds, not hours so refresh every 24 seconds for daily
#REFRESH_DAILY=24
#REFRESH_EVERY_4_HOURS=4

def authorize(dn, username, acctgroup, acctrole='Analysis',age_limit=3600):
    # TODO: Break this into smaller functions. Krb5 related code 
    #       should be split out
    creds_base_dir = os.environ.get('JOBSUB_CREDENTIALS_DIR')
    krb5cc_dir = jobsub.get_jobsub_krb5cc_dir()
    try:
        principal = '%s/batch/fifegrid@FNAL.GOV' % username
        real_cache_fname = os.path.join(krb5cc_dir, 'krb5cc_%s'%username)
        old_cache_fname = os.path.join(krb5cc_dir, 'old_krb5cc_%s'%username)
        keytab_fname = os.path.join(creds_base_dir, '%s.keytab'%username)
        x509_cache_fname = x509_proxy_fname(username, acctgroup, acctrole)
        x509_user_cert = os.path.join(jobsub.get_jobsub_certs_dir(),
                                      '%s.cert'%username)
        x509_user_key = os.path.join(jobsub.get_jobsub_certs_dir(),
                                     '%s.key'%username)

        # Create the proxy as a temporary file in tmp_dir and perform a
        # privileged move on the file.
        x509_tmp_prefix = os.path.join(jobsub.get_jobsub_tmp_dir(),
                                       os.path.basename(x509_cache_fname))
        x509_tmp_file = NamedTemporaryFile(prefix='%s_'%x509_tmp_prefix,
                                           delete=False)
        x509_tmp_fname = x509_tmp_file.name
        x509_tmp_file.close()

        # If the x509_cache_fname is new enough skip everything and use it
        # needs_refresh only looks for file existance and stat. It works on
        # proxies owned by other users as well.
        if needs_refresh(x509_cache_fname):
            # First check if need to use keytab/KCA robot keytab
            if os.path.exists(keytab_fname):
                if not is_valid_cache(real_cache_fname):
                    new_cache_file = NamedTemporaryFile(prefix="%s_"%real_cache_fname,delete=False)
                    new_cache_fname = new_cache_file.name
                    logger.log("new_cache_fname=%s"%new_cache_fname)
	            new_cache_file.close()
                    logger.log('Creating krb5 ticket ...')
                    krb5_ticket = Krb5Ticket(keytab_fname, new_cache_fname, principal)
                    krb5_ticket.create()
                    logger.log('Creating krb5 ticket ... DONE')

                    # Rename is atomic and silently overwrites destination
                    if os.path.exists(new_cache_fname):
                         os.rename(new_cache_fname, real_cache_fname)

                krb5cc_to_vomsproxy(real_cache_fname, x509_tmp_fname,
                                    acctgroup, acctrole)
            elif( os.path.exists(x509_user_cert) and
                  os.path.exists(x509_user_key) ):
                # Convert x509 cert-key pair to voms proxy
                x509pair_to_vomsproxy(x509_user_cert, x509_user_key,
                                      x509_tmp_fname, acctgroup,
                                      acctrole=acctrole)
            else:
                # No source credentials found for this user.
                logger.log('Unable to find Kerberoes keytab file or a X509 cert-key pair for user %s' % (username))
                raise AuthorizationError(dn, acctgroup)

            exe = jobsub.get_jobsub_priv_exe()
            cmd = '%s moveFileAsUser "%s" "%s" "%s"' % (exe, x509_tmp_fname,
                                                        x509_cache_fname,
                                                        username)
            err = ''
            logger.log(cmd)
            try:
                out, err = subprocessSupport.iexe_priv_cmd(cmd)
            except:
                logger.log('Error moving file as user using command %s: %s' % (cmd, err))
                raise

        return x509_cache_fname
    except:
        logger.log('EXCEPTION OCCURED IN AUTHORIZATION')
        logger.log(traceback.format_exc())
        raise AuthorizationError(dn, acctgroup)


def is_valid_cache(cache_name):
    klist_exe=spawn.find_executable("klist")
    cmd ="%s -s -c %s"%(klist_exe,cache_name)
    try:
        logger.log(cmd)
        cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd)
        logger.log("%s is still valid"%cache_name)
        return True
    except:
        logger.log("%s is expired,invalid, or does not exist"%cache_name)
        return False

def create_voms_proxy(dn, acctgroup, role):
    logger.log('create_voms_proxy: Authenticating DN: %s' % dn)
    username = authenticate(dn, acctgroup, role)
    logger.log('create_voms_proxy: Authorizing user: %s' % username)
    voms_proxy = authorize(dn, username, acctgroup, role)
    logger.log('User authorized. Voms proxy file: %s' % voms_proxy)
    return (username, voms_proxy)


def refresh_proxies(agelimit=3600):
    cmd = 'condor_q -format "%s^" accountinggroup -format "%s^" x509userproxysubject -format "%s\n" x509userproxy '
    already_processed=['']
    queued_users=[]
    cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd)
    if cmd_err:
        raise Exception("command %s returned %s"%(cmd,cmd_err))
    lines = cmd_out.split("\n")
    for line in lines:
        if line not in already_processed:
            already_processed.append(line)
            check=line.split("^")
            if len(check)==3:
                try:
                    ac_grp=check[0]
                    dn=check[1]
                    grp,user=ac_grp.split(".")
                    if user not in queued_users:
                        queued_users.append(user)
                    grp=grp.replace("group_","")
		    proxy_name=os.path.basename(check[2])
		    x,uid,role=proxy_name.split('_')	
                    print "checking proxy %s %s %s %s"%(dn,user,grp,role)
                    authorize(dn,user,grp,role,agelimit)
                except:
                    logger.log("Error processing %s"%line)
                    logger.log("%s"%sys.exc_info()[1])
    #todo: invalidate old proxies
    #one_day_ago=int(time.time())-86400
    #condor_history -format "%s^" accountinggroup \
    #-format "%s^" x509userproxysubject -format "%s\n" owner \
    #-constraint 'EnteredCurrentStatus > one_day_ago'
    #can be checked against already_processed list to remove x509cc_(user)
    #if user not in queued_users remove krb5cc_(user) and (user).keytab


def _check_auth(dn, acctgroup, role):
    return create_voms_proxy(dn, acctgroup, role)


def check_auth(func):
    def check_auth_wrapper(self, acctgroup, *args, **kwargs):
        logger.log(traceback=True)
        dn = cherrypy.request.headers.get('Auth-User')
        err = ''
        if dn and acctgroup:
            logger.log('DN: %s, acctgroup: %s ' % (dn, acctgroup))
            try:
                role = 'Analysis'
                tokens = acctgroup.split('--ROLE--')
                if len(tokens) > 1:
                    (acctgroup, role) = tokens[0:2]
                    logger.log('found ROLE %s in %s' %(role,tokens))
                username, voms_proxy =  _check_auth(dn, acctgroup, role)
                if username and voms_proxy:
                    kwargs['role'] = role
                    kwargs['username'] = username
                    kwargs['voms_proxy'] = voms_proxy
                    return func(self, acctgroup, *args, **kwargs)
                else:
                    # return error for failed auth
                    err = 'User authorization has failed: %s'%sys.exc_info()[1]
                    cherrypy.response.status = 401
                    logger.log(err)
                    rc = {'err': err}
            except:
                # return error for failed auth
                err = 'User authorization has failed: %s'% sys.exc_info()[1]
                cherrypy.response.status = 401
                logger.log(err)
                rc = {'err': err}
        else:
            # return error for no subject_dn and acct group
            err = 'User has not supplied subject DN and/or accounting group:%s'%sys.exc_info()[1]
            logger.log(err)
            rc = {'err': err}
            cherrypy.response.status = 401
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
            if len(sys.argv)>=3:
                refresh_proxies(sys.argv[2])
            else:
                refresh_proxies()
