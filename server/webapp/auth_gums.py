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

import logger
import logging
import jobsub
import subprocessSupport
import auth


def authenticate(dn, acctgroup, acctrole):
    """Check if DN, accounting group, and role is
       in GUMS database
    """
    try:
        fqan = auth.get_voms_fqan(acctgroup, acctrole)
        username = get_gums_mapping(dn, fqan)
        username = username.strip()
        logger.log("GUMS mapped dn '%s' fqan '%s' to '%s'" %
                   (dn, fqan, username))
        return username
    except:
        err = "GUMS mapping for the dn '%s' fqan '%s' failed" % (dn, fqan)
        logger.log(err, traceback=True, severity=logging.ERROR)
        logger.log(err, traceback=True,
                   severity=logging.ERROR, logfile='error')
    raise auth.AuthenticationError(dn, acctgroup)

def get_gums_mapping(dn, fqan):
    """find user mapped to input dn
    """
    exe = jobsub.get_jobsub_priv_exe()
    # get rid of all the /CN=133990 and /CN=proxy for gums mapping
    # is this kosher?  how would a bad guy defeat this?
    #
    dn = auth.clean_proxy_dn(dn)
    cmd = '%s getMappedUsername "%s" "%s"' % (exe, dn, fqan)
    err = ''
    logger.log(cmd)
    try:
        out, err = subprocessSupport.iexe_priv_cmd(cmd)
    except:
        err = 'Error running command %s: %s' % (cmd, err)
        logger.log(err, severity=logging.ERROR)
        logger.log(err, severity=logging.ERROR, logfile='error')
        raise
    return out

