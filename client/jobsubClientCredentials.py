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
    def __init__(self):
       Exception.__init__(self, "Credentials not found")


class CredentialsError(Exception):
    def __init__(self):
       Exception.__init__(self, "Credentials erorr")


class Credentials():
    """
    Abstract Class for Credentials
    """

    def __init__(self):
        pass

    def isValid(self):
        raise NotImplementedError

    def exists(self):
        raise NotImplementedError


class Krb5Ticket(Credentials):

    def __init__(self):
        Credentials.__init__(self)
        try:
            self.krb5CredCache = self.getKrb5CredCache()
            lt = krb5_ticket_lifetime(self.krb5CredCache)
            self.validFrom = lt['stime']
            self.validTo = lt['etime']
        except:
            raise
            self.krb5CredCache = None
            self.validFrom = None
            self.validTo = None


    def __str__(self):
        return '%s' % {
            'KRB5CCNAME': self.krb5CredCache,
            'VALID_FROM': self.validFrom,
            'VALID_TO'  : self.validTo
        }


    def getKrb5CredCache(self):
        cache_file = None

        #if not is_os_linux():
        #    raise CredentialsNotFoundError()

        krb5_cc = constants.KRB5_DEFAULT_CC
        if ('KRB5CCNAME' in os.environ):
            krb5_cc = os.environ.get('KRB5CCNAME')

        cache_file = krb5_cc.split(':')[-1]

        if not os.path.exists(cache_file):
            raise CredentialsNotFoundError()

        return cache_file


    def isValid(self):
        # A crude check. Need to find libraries to do it.
        if self.exists() and not self.expired():
            return True
        return False


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
        raise Exception("Unable to find command 'kx509' in the PATH.\nSTDERR:\n%s"%klist_err)

    cmd = '%s -o %s' % (kx509_cmd, x509_fname)
    cmd_env = {'KRB5CCNAME': krb5cc}
    klist_out, klist_err = subprocessSupport.iexe_cmd(cmd, child_env=cmd_env)


def krb5_ticket_lifetime(cache):
    klist_cmd = spawn.find_executable("klist")
    if not klist_cmd:
        raise Exception("Unable to find command 'klist' in the PATH")
    cmd = '%s -c %s' % (klist_cmd, cache)
    klist_out, klist_err = subprocessSupport.iexe_cmd(cmd)
    lt = (re.findall(constants.KRB5TICKET_VALIDITY_HEADER, klist_out))[0]
    return {'stime': ' '.join(lt.split()[:2]),
            'etime': ' '.join(lt.split()[2:4])}

# Simple tests that work on Linux
#k = Krb5Ticket()
#print k
#print 'VALID: %s' % k.isValid()
