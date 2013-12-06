#!/usr/bin/env python

import os
import time
import sys
import re

import constants
import subprocessSupport

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
            'VALID FROM': self.validFrom,
            'VALID TO'  : self.validTo
        }


    def getKrb5CredCache(self):
        if is_os_linux():
            return os.environ.get('KRB5CCNAME').split(':')[-1]
        #elif is_os_macosx():
        #    # TODO: Figure out how to check if the ticket exists on OSX
        #    return True
        #else:
        #    print 'ERROR: Unsupported platform %s' % platform.system()
        #    return False
        raise CredentialsNotFoundError()


    def isValid(self):
        # A crude check. Need to find libraries to do it.
        if self.exists() and not self.expired():
            return True
        return False


    def exists(self):
        if self.krb5CredCache:
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


def krb5_ticket_lifetime(cache):
    klist_cmd = jobsubUtils.which('klist')
    if klist_cmd:
        cmd = '%s -c %s' % (klist_cmd, cache)
        klist_out = subprocessSupport.iexe_cmd(cmd)
        lt = re.findall(constants.KRB5TICKET_VALIDITY_HEADER, klist_out)[0]
        return {'stime': ' '.join(lt.split()[:2]), 'etime': ' '.join(lt.split()[2:4])}
    raise Exception("Unable to find command 'klist' in the PATH")

# Simple tests that work on Linux
#k = Krb5Ticket()
#print k
#print 'VALID: %s' % k.isValid()
