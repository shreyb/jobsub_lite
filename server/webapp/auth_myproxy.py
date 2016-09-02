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

import os
import traceback
import logger
import logging
import jobsub
import subprocessSupport
import auth

from distutils import spawn
from tempfile import NamedTemporaryFile
from JobsubConfigParser import JobsubConfigParser


def authorize(dn, username, acctgroup, acctrole=None, age_limit=3600):
    """ Pull a proxy from the myproxy server
    """
    #logger.log("dn %s , username %s , acctgroup %s, acctrole %s ,age_limit %s"%(dn, username, acctgroup, acctrole,age_limit))
    jobsubConfig = jobsub.JobsubConfig()

    creds_base_dir = os.environ.get('JOBSUB_CREDENTIALS_DIR')
    x509_cache_fname = auth.x509_proxy_fname(username, acctgroup, acctrole)
    x509_tmp_prefix = os.path.join(jobsubConfig.tmpDir,
                                   os.path.basename(x509_cache_fname))
    x509_tmp_file = NamedTemporaryFile(prefix='%s_' % x509_tmp_prefix,
                                       delete=False)
    x509_tmp_fname = x509_tmp_file.name
    x509_tmp_file.close()
    try:
        if auth.needs_refresh(x509_cache_fname, age_limit):

            if jobsub.should_transfer_krb5cc(acctgroup):
                refresh_krb5cc(username)

            p = JobsubConfigParser()
            myproxy_exe = spawn.find_executable("myproxy-logon")
            vomsproxy_exe = spawn.find_executable("voms-proxy-info")
            myproxy_server = p.get('default', 'myproxy_server')
            child_env = os.environ.copy()
            child_env['X509_USER_CERT'] = child_env['JOBSUB_SERVER_X509_CERT']
            child_env['X509_USER_KEY'] = child_env['JOBSUB_SERVER_X509_KEY']
            dn = auth.clean_proxy_dn(dn)
            cmd = "%s -n -l '%s' -s %s -t 24 -o %s" %\
                (myproxy_exe, dn, myproxy_server, x509_tmp_fname)
            logger.log('%s' % cmd)
            out, err = subprocessSupport.iexe_cmd(cmd, child_env=child_env)
            logger.log('out= %s' % out)
            if err:
                logger.log(err, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')
            auth.x509pair_to_vomsproxy(
                x509_tmp_fname, x509_tmp_fname, x509_tmp_fname, acctgroup, acctrole)

            cmd2 = "%s  -all -file %s " % (vomsproxy_exe, x509_tmp_fname)
            logger.log(cmd2)
            out2, err2 = subprocessSupport.iexe_cmd(cmd2)
            if not acctrole:
                acctrole = jobsub.default_voms_role(acctgroup)
            sub_group_pattern = jobsub.sub_group_pattern(acctgroup)
            search_pat = "%s/Role=%s/Capability" % (
                sub_group_pattern, acctrole)

            if (search_pat in out2) and ('VO' in out2):
                logger.log('found  %s , authenticated successfully' %
                           (search_pat))
                jobsub.move_file_as_user(
                    x509_tmp_fname, x509_cache_fname, username)
            else:
                logger.log('failed to find %s in %s' % (search_pat, out2))
                t1 = search_pat in out2
                t2 = 'VO' in out2
                logger.log('test (%s in out2)=%s test(VO in out2)=%s' %
                           (search_pat, t1, t2))
                os.remove(x509_tmp_fname)

                err = "unable to authenticate with role='%s'.  Is this a typo?" % acctrole
                logger.log(err, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')

                raise auth.OtherAuthError(err)

    except:
        err = traceback.format_exc()
        logger.log(err, severity=logging.ERROR)
        logger.log(err, severity=logging.ERROR, logfile='error')
        raise auth.AuthorizationError(dn, acctgroup)
    if os.path.exists(x509_tmp_fname):
        os.remove(x509_tmp_fname)
        logger.log("cleanup:rm %s" % x509_tmp_fname)

    return x509_cache_fname

