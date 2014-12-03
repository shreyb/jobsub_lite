#!/usr/bin/env python

import os
import time
import sys
import re
from distutils import spawn

import constants
import subprocessSupport
import jobsubUtils

class CredentialsNotFoundError(Exception):
    def __init__(self,errMsg="Credentials not found. Try running kinit first."):
       sys.exit(errMsg)
       Exception.__init__(self, errMsg)


class CredentialsError(Exception):
    def __init__(self, errMsg="Credentials eror"):
       Exception.__init__(self, errMsg)


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
            raise


    def exists(self):
        if (self.cert and self.key and
            os.path.exists(self.cert) and os.path.exists(self.key)):
            return True
        return False


    def expired(self):
        if not self.exists():
            raise CredentialsNotFoundError()
        now = time.time()
        stime = time.mktime(time.strptime(self.validFrom, '%b %d %H:%M:%S %Y %Z'))
        etime = time.mktime(time.strptime(self.validTo, '%b %d %H:%M:%S %Y %Z'))
        if (stime < now) and (now < etime):
            return False
        return True


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

        if proxy_file and os.path.exists(proxy_file):
            raise CredentialsNotFoundError()

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
            raise Exception("Unable to find command 'voms-proxy-info' in the PATH.")

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
        except:
            self.krb5CredCache = None
            self.validFrom = None
            self.validTo = None
            raise


    def __str__(self):
        return '%s' % {
            'KRB5CCNAME': self.krb5CredCache,
            'VALID_FROM': self.validFrom,
            'VALID_TO'  : self.validTo
        }


    def getKrb5CredCache(self):

        krb5_cc = os.environ.get('KRB5CCNAME', constants.KRB5_DEFAULT_CC)
        cache_file = krb5_cc.split(':')[-1]

        if not os.path.exists(cache_file):
            raise CredentialsNotFoundError()

        return cache_file


    def exists(self):
        if self.krb5CredCache and os.path.exists(self.krb5CredCache):
            return True
        return False


    def expired(self):
        if not self.krb5CredCache:
            raise CredentialsNotFoundError()
        now = time.time()
        stime = time.mktime(time.strptime(self.validFrom, '%m/%d/%y %H:%M:%S'))
        etime = time.mktime(time.strptime(self.validTo, '%m/%d/%y %H:%M:%S'))
        if (stime < now) and (now < etime):
            return False
        return True


def krb5cc_to_x509(krb5cc, x509_fname=constants.X509_PROXY_DEFAULT_FILE):
    kx509_cmd = spawn.find_executable("kx509")
    if not kx509_cmd:
        raise Exception("Unable to find command 'kx509' in the PATH")

    cmd = '%s -o %s' % (kx509_cmd, x509_fname)
    cmd_env = {'KRB5CCNAME': krb5cc}
    cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd, child_env=cmd_env)


def krb5_ticket_lifetime(cache):
    klist_cmd = spawn.find_executable("klist")
    if not klist_cmd:
        raise Exception("Unable to find command 'klist' in the PATH")
    cmd = '%s -c %s' % (klist_cmd, cache)
    cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd)
    lt = (re.findall(constants.KRB5TICKET_VALIDITY_HEADER, cmd_out))[0]
    return {'stime': ' '.join(lt.split()[:2]),
            'etime': ' '.join(lt.split()[2:4])}

def x509_lifetime(cert):
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


# Simple tests that work on Linux
#k = Krb5Ticket()
#print k
#print 'VALID: %s' % k.isValid()
