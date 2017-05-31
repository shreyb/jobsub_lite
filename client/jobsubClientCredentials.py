#!/usr/bin/env python

import os
import time
import sys
import re
from distutils import spawn
from tempfile import NamedTemporaryFile
import traceback
import logSupport
import constants
import subprocessSupport
import jobsubUtils
import jobsubClient


class CredentialsNotFoundError(Exception):

    def __init__(self, errMsg=''.join(["Cannot find credentials to use. ",
                                       "Run 'kinit' to get a valid kerberos ",
                                       "ticket or set X509 credentials ",
                                       "related variables"])):
        logSupport.dprint(traceback.format_exc())
        # sys.exit(errMsg)


class CredentialsError(Exception):

    def __init__(self, errMsg="Credentials eror"):
        logSupport.dprint(traceback.format_exc())
        sys.exit(errMsg)


class Credentials():
    """
    Abstract Class for Credentials
    """

    def __init__(self):
        pass

    def isValid(self):
        # A crude check. Need to find libraries to do it.
        if self.exists() and not self.expired():
            return True
        return False

    def exists(self):
        raise NotImplementedError

    def expired(self):
        raise NotImplementedError


class X509Credentials(Credentials):

    def __init__(self, cert, key):
        Credentials.__init__(self)
        self.cert = cert
        self.key = key

        try:
            lt = x509_lifetime(self.cert)
            self.validFrom = lt['stime']
            self.validTo = lt['etime']
        except:
            self.validFrom = None
            self.validTo = None
            raise CredentialsError

    def exists(self):
        if self.cert and self.key \
                and os.path.exists(self.cert) \
                and os.path.exists(self.key):
            return True
        return False

    def expired(self):
        if not self.exists():
            raise CredentialsNotFoundError
        now = time.mktime(time.gmtime())
        try:
            fmt = '%b %d %H:%M:%S %Y %Z'
            stime = time.mktime(time.strptime(self.validFrom, fmt))
            etime = time.mktime(time.strptime(self.validTo, fmt))
            if (stime < now) and (now < etime):
                return False
            return True
        except:
            err = ''.join(["error parsing X509 certificate start time:",
                           "%s or end time:%s" % (self.validFrom, self.validTo)])
            raise CredentialsError(err)


class X509Proxy(X509Credentials):

    def __init__(self, proxy_file=None):
        if proxy_file:
            self.proxyFile = proxy_file
        else:
            self.proxy_file = self.getDefaultProxyFile()

        X509Credentials.__init__(self, cert=self.proxyFile, key=self.proxyFile)

    def getDefaultProxyFile(self):
        proxy_file = os.environ.get('X509_USER_PROXY',
                                    constants.X509_PROXY_DEFAULT_FILE)

        if proxy_file and not os.path.exists(proxy_file):
            err = "Proxy file %s not found. Try running cigetcert " % proxy_file
            err += "or setting X509 credentials related environment variables"
            raise CredentialsNotFoundError(err)

        return proxy_file


class VOMSProxy(X509Proxy):

    def __init__(self, proxy_file=None):
        X509Proxy.__init__(self, proxy_file=proxy_file)
        try:
            self.fqan = self.getFQAN()
        except:
            self.fqan = None

    def getFQAN(self):
        voms_cmd = spawn.find_executable("voms-proxy-info")
        if not voms_cmd:
            wrn = "Unable to find command 'voms-proxy-info' in the PATH, "
            wrn += "used to verify  accounting role(s). Continuing."
            print wrn
            return []

        cmd = '%s -file %s -fqan' % (voms_cmd, self.proxyFile)
        fqan = []
        try:
            cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd)
            fqan = cmd_out.strip().splitlines()
        except:
            pass
        return fqan


class Krb5Ticket(Credentials):

    def __init__(self):
        Credentials.__init__(self)
        try:
            self.krb5CredCache = self.getKrb5CredCache()
            lt = krb5_ticket_lifetime(self.krb5CredCache)
            self.validFrom = lt['stime']
            self.validTo = lt['etime']
            self.principal = krb5_default_principal(self.krb5CredCache)
        except:
            self.krb5CredCache = None
            self.validFrom = None
            self.validTo = None
            self.principal = None
            # logSupport.dprint(traceback.format_exc())
            raise CredentialsNotFoundError('no valid Krb5 cache found')

    def __str__(self):
        return '%s' % {
            'KRB5CCNAME': self.krb5CredCache,
            'VALID_FROM': self.validFrom,
            'VALID_TO': self.validTo,
            'DEFAULT_PRINCIPAL': self.principal,
        }

    def getKrb5CredCache(self):

        krb5_cc = os.environ.get('KRB5CCNAME', constants.KRB5_DEFAULT_CC)
        cache_file = krb5_cc.split(':')[-1]
        cache_type = krb5_cc.split(':')[0]

        if cache_type == cache_file or cache_type == 'FILE':
            if not os.path.exists(cache_file):
                raise CredentialsNotFoundError("%s not found" % cache_file)
            return cache_file

        if cache_type == 'API':
            return krb5_cc
        err = "don't know how to handle krb5 credential type '%s'" % krb5_cc
        raise CredentialsNotFoundError(err)

    def exists(self):
        if self.krb5CredCache:
            if 'API:' in self.krb5CredCache:
                return True
            else:
                if os.path.exists(self.krb5CredCache):
                    return True
        return False

    def expired(self):
        if not self.exists():
            raise CredentialsNotFoundError
        now = time.time()
        fmts = ['%m/%d/%y %H:%M:%S',
                '%m/%d/%Y %H:%M:%S',
                '%b %d %H:%M:%S %Y',
                ]
        for fmt in fmts:
            try:
                stime = time.mktime(time.strptime(self.validFrom, fmt))
                etime = time.mktime(time.strptime(self.validTo, fmt))
            except:
                pass
        try:
            if (stime < now) and (now < etime):
                return False
            return True
        except:
            err = "error parsing KRB5 ticket start time:%s or end time:%s" %\
                (self.validFrom, self.validTo)
            raise CredentialsError(err)


def mk_temp_fname(fname):
    tmp_file = NamedTemporaryFile(prefix="%s_" % fname, delete=True)
    tmp_fname = tmp_file.name
    tmp_file.close()
    return tmp_fname


def krb5cc_to_x509(krb5cc, x509_fname=constants.X509_PROXY_DEFAULT_FILE):

    kx509_cmd = spawn.find_executable("kx509")
    tmp_x509_fname = mk_temp_fname(x509_fname)
    proxy_created = False
    try:
        cmd = '%s -o %s' % (kx509_cmd, tmp_x509_fname)
        cmd_env = {'KRB5CCNAME': krb5cc}
        cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd, cmd_env)
        os.rename(tmp_x509_fname, x509_fname)
        proxy_created = True
    except:
        pass
    if not proxy_created:
        raise CredentialsError("failed to create %s using kx509" % x509_fname)


def krb5_default_principal(cache=None):
    try:
        if not cache:
            cache = Krb5Ticket().krb5CredCache
        klist_cmd = spawn.find_executable("klist")
        if not klist_cmd:
            raise Exception("Unable to find command 'klist' in the PATH")
        cmd = '%s -c %s' % (klist_cmd, cache)
        cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd)
        prn = (re.findall(
            constants.KRB5TICKET_DEFAULT_PRINCIPAL_PATTERN, cmd_out))[0]
    except:
        print sys.exc_info()[1]
        prn = "UNKNOWN"
    return prn


def server_hostname(server):

    serverParts = server.split(':')

    if len(serverParts) == 1:
        return server
    elif len(serverParts) > 1:
        if serverParts[0].startswith('http'):
            server = serverParts[1]
        else:
            server = serverParts[0]
    server = server.replace('/', '')
    return server


def cigetcert_to_x509_cmd(server, acctGroup=None, debug=None):

    default_proxy_file = default_proxy_filename(acctGroup)
    proxy_file = os.environ.get('X509_USER_PROXY', default_proxy_file)
    issuer = proxy_issuer(proxy_file)

    server = server_hostname(server)
    cigetcert_cmd = spawn.find_executable("cigetcert")
    if not cigetcert_cmd:
        err = "ERROR: Server %s wants to use cigetcert to authenticate, " % server
        err += "but Unable to find command 'cigetcert' in the PATH"
        raise CredentialsError(err)
    cmd = "%s -s %s -n -o %s" % (cigetcert_cmd, server, proxy_file)
    logSupport.dprint(cmd)
    return cmd


def cigetcert_to_x509(server, acctGroup=None, debug=None):

    cmd = cigetcert_to_x509_cmd(server, acctGroup, debug)
    default_proxy_file = default_proxy_filename(acctGroup)
    proxy_file = os.environ.get('X509_USER_PROXY', default_proxy_file)
    cmd_out = cmd_err = ""
    child_env = os.environ.copy()
    child_env['X509_CERT_DIR'] = jobsubClient.get_capath()
    try:
        cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd, child_env=child_env)
    except:
        err = "%s %s" % (cmd_err, sys.exc_info()[1])
        raise CredentialsNotFoundError(err)
    logSupport.dprint("stdout: %s" % cmd_out)
    logSupport.dprint("stderr: %s" % cmd_err)
    if len(cmd_err):
        print 'error: %s' % cmd_err
        return ""
    return proxy_file


def krb5_ticket_lifetime(cache):
    klist_cmd = spawn.find_executable("klist")
    if not klist_cmd:
        raise Exception("Unable to find command 'klist' in the PATH")
    cmd = '%s -c %s' % (klist_cmd, cache)
    cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd)
    lt = (re.findall(constants.KRB5TICKET_VALIDITY_HEADER, cmd_out))[0]
    vstring = lt[2]
    date_parts = vstring.split()
    ld = len(date_parts)
    mid = ld / 2

    ltdict = {'stime': ' '.join(date_parts[:mid]),
              'etime': ' '.join(date_parts[mid:ld - 1])}
    logSupport.dprint('ltdict=%s' % ltdict)
    return ltdict


def x509_lifetime(cert):
    if not os.path.exists(cert):
        raise CredentialsNotFoundError(
            'cert or proxy file %s not found' % cert)
    openssl_cmd = spawn.find_executable("openssl")
    if not openssl_cmd:
        raise Exception("Unable to find command 'openssl' in the PATH")
    cmd = '%s x509 -in %s -noout -startdate -enddate' % (openssl_cmd, cert)
    cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd)
    lt = {'stime': None, 'etime': None}
    for line in cmd_out.strip().splitlines():
        if line.startswith('notBefore='):
            lt['stime'] = line[10:]
        elif line.startswith('notAfter='):
            lt['etime'] = line[9:]
    return lt


def default_proxy_filename(acctGroup=None):
    return constants.X509_PROXY_DEFAULT_FILE


def proxy_issuer(proxy_fname):
    openssl_cmd = spawn.find_executable("openssl")
    issuer = ""
    if not openssl_cmd:
        raise Exception("Unable to find command 'openssl' in the PATH.")
    cmd = '%s x509 -in %s -noout -issuer' % (openssl_cmd, proxy_fname)
    try:
        cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd)
        issuer = cmd_out.strip()
    except:
        pass
    return issuer

if __name__ == '__main__':
    # Simple tests that work on SL5,6,7, OSX 10
    for a in sys.argv:
        if a == '--debug':
            logSupport.init_logging(True)
    k = Krb5Ticket()
    print k
    print 'VALID: %s' % k.isValid()
