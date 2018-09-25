#!/usr/bin/env python
"""
 Description:
   This module implements the JobSub gums  authN/authZ functionailty.

 Project:
   JobSub

 Author:
   Parag Mhashilkar

"""

import logger
import logging
import jobsub
import subprocessSupport
import authutils


def authenticate(dn, acctgroup, acctrole):
    """Check if this combination in GUMS database
       Args:
                  dn: DN of proxy or cert trying to authenticate
           acctgroup: accounting group (experiment)
            acctrole: role (Analysis, Production, etc)
    """
    try:
        fqan = get_voms_fqan(acctgroup, acctrole)
        username = get_gums_mapping(dn, fqan)
        username = username.strip()
        logger.log("GUMS mapped dn '%s' fqan '%s' to '%s'" %
                   (dn, fqan, username))
        return username
    except Exception:
        err = "GUMS mapping for the dn '%s' fqan '%s' failed" % (dn, fqan)
        logger.log(err, traceback=True, severity=logging.ERROR)
        logger.log(err, traceback=True,
                   severity=logging.ERROR, logfile='error')
    raise authutils.AuthenticationError(dn, acctgroup)


def get_gums_mapping(dn, fqan):
    """find user mapped to input combo
       Args:
             dn: DN of proxy or cert trying to authenticate
           fqan: combination of acctgroup/role
    """
    exe = jobsub.get_jobsub_priv_exe()
    # get rid of all the /CN=133990 and /CN=proxy for gums mapping
    # is this kosher?  how would a bad guy defeat this?
    #
    dn = authutils.clean_proxy_dn(dn)
    cmd = '%s getMappedUsername "%s" "%s"' % (exe, dn, fqan)
    err = ''
    logger.log(cmd)
    try:
        out, err = subprocessSupport.iexe_priv_cmd(cmd)
    except Exception:
        err = 'Error running command %s: %s' % (cmd, err)
        logger.log(err, severity=logging.ERROR)
        logger.log(err, severity=logging.ERROR, logfile='error')
        raise
    return out


def get_voms_fqan(acctgroup, acctrole=None):
    """return the fqan from the VOMS string
    """
    attrs = authutils.get_voms_attrs(acctgroup, acctrole=acctrole).split(':')
    return attrs[-1]
