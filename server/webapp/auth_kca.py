#!/usr/bin/env python
"""
 Description:
   This module implements the JobSub webapp authN/authZ functionailty.
   Some code and functionality is taken from CDFCAF

 Project:
   JobSub

 Author:
   Parag Mhashilkar

"""

import os
import re
import logger
import logging
import jobsub
import auth

from tempfile import NamedTemporaryFile

def authenticate(dn):
    """check DN against supported patterns, extract username
    """
    KCA_DN_PATTERN_LIST = os.environ.get('KCA_DN_PATTERN_LIST')
    logger.log("dns patterns supported:%s " % KCA_DN_PATTERN_LIST)

    for pattern in KCA_DN_PATTERN_LIST.split(','):
        username = re.findall(pattern, dn)
        if len(username) >= 1 and username[0] != '':
            return username[0]
    err = 'failed to authenticate:%s' % dn
    logger.log(err, severity=logging.ERROR)
    logger.log(err, severity=logging.ERROR, logfile='error')
    raise auth.AuthenticationError(err)


def authorize(dn, username, acctgroup, acctrole=None, age_limit=3600):
    """Authorize using FNAL KCA
       Args:
                dn: DN of proxy or cert trying to authorize
          username: uid of user 
         acctgroup: account group (experiment)
          acctrole: role (Analysis Production etc)
         age_limit: maximum age in seconds or existing proxy before
                    forced refresh
    """
    logger.log("dn %s username %s acctgroup %s acctrole %s age_limit %s" %
               (dn, username, acctgroup, acctrole, age_limit))
    jobsubConfig = jobsub.JobsubConfig()
    creds_base_dir = os.environ.get('JOBSUB_CREDENTIALS_DIR')
    # Create the proxy as a temporary file in tmp_dir and perform a
    # privileged move on the file.
    x509_cache_fname = auth.x509_proxy_fname(username, acctgroup, acctrole)
    x509_tmp_prefix = os.path.join(jobsubConfig.tmpDir,
                                   os.path.basename(x509_cache_fname))
    x509_tmp_file = NamedTemporaryFile(prefix='%s_' % x509_tmp_prefix,
                                       delete=False)
    x509_tmp_fname = x509_tmp_file.name
    x509_tmp_file.close()
    try:
        keytab_fname = os.path.join(creds_base_dir, '%s.keytab' % username)
        x509_user_cert = os.path.join(jobsubConfig.certsDir,
                                      '%s.cert' % username)
        x509_user_key = os.path.join(jobsubConfig.certsDir,
                                     '%s.key' % username)

        # If the x509_cache_fname is new enough skip everything and use it
        # needs_refresh only looks for file existance and stat. It works on
        # proxies owned by other users as well.
        if auth.needs_refresh(x509_cache_fname, age_limit):
            # First check if need to use keytab/KCA robot keytab
            if os.path.exists(keytab_fname):
                real_cache_fname = auth.refresh_krb5cc(username)
                auth.krb5cc_to_vomsproxy(real_cache_fname, x509_tmp_fname,
                                    acctgroup, acctrole)
            elif(os.path.exists(x509_user_cert) and
                 os.path.exists(x509_user_key)):
                # Convert x509 cert-key pair to voms proxy
                auth.x509pair_to_vomsproxy(x509_user_cert, x509_user_key,
                                      x509_tmp_fname, acctgroup,
                                      acctrole=acctrole)
            else:
                # No source credentials found for this user.
                err = ''.join(["Unable to find Kerberoes keytab file or X509 ",
                               "cert-key pair for user %s" % (username),
                               "dn = %s acctgroup =%s" % (dn, acctgroup), ])
                logger.log(err)
                raise auth.OtherAuthError(err)

            jobsub.move_file_as_user(
                x509_tmp_fname, x509_cache_fname, username)

    except Exception, e:
        logger.log(str(e), severity=logging.ERROR)
        logger.log(str(e), severity=logging.ERROR, logfile='error')
        raise
    finally:
        if os.path.exists(x509_tmp_fname):
            os.remove(x509_tmp_fname)
            logger.log("cleanup:rm %s" % x509_tmp_fname)
    return x509_cache_fname

