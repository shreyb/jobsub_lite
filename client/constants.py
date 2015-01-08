#!/usr/bin/env python

################################################################################
# Project:
#   JobSub
#
# Author:
#   Parag Mhashilkar
#
# Description:
#   This module implements constants used by the JobSub Client
#
################################################################################

import os

################################################################################
# JOBSUB Constants
################################################################################

#Version strings to be set by release.py
__rpmversion__='__VERSION__'
__rpmrelease__='__RELEASE__'


# Default JobSub Server
JOBSUB_SERVER_DEFAULT_PORT = 8443
JOBSUB_SERVER_URL_PATTERN = 'https://%s:%s'
JOBSUB_SERVER = os.environ.get('JOBSUB_SERVER',
                               'https://fifebatch.fnal.gov:8443')
#JOBSUB_SERVER_LIST = ['https://fermicloud136.fnal.gov:8443','https://fermicloud137.fnal.gov:8443']
# Default JobSub job submission url pattern
# https://server.com:8443/jobsub/api/<api-version>/acctgroups/<exp-name>/jobs/

JOBSUB_JOB_SUBMIT_URL_PATTERN = '%s/jobsub/acctgroups/%s/jobs/'
JOBSUB_DAG_SUBMIT_URL_PATTERN = '%s/jobsub/acctgroups/%s/jobs/dag/'
JOBSUB_DAG_HELP_URL_PATTERN = '%s/jobsub/acctgroups/%s/jobs/dag/help/'
#JOBSUB_JOB_SUBMIT_URL_PATTERN = '%s/jobsub/acctgroups/%s/jobs/'
JOBSUB_JOB_SUBMIT_URL_PATTERN_WITH_ROLE = '%s/jobsub/acctgroups/%s--ROLE--%s/jobs/'
JOBSUB_DAG_SUBMIT_URL_PATTERN_WITH_ROLE = '%s/jobsub/acctgroups/%s--ROLE--%s/jobs/dag/'

JOBSUB_Q_NO_GROUP_URL_PATTERN = '%s/jobsub/jobs/'
JOBSUB_Q_USERID_URL_PATTERN = '%s/jobsub/users/%s/jobs/'
JOBSUB_Q_SUMMARY_URL_PATTERN = '%s/jobsub/jobs/summary/'
JOBSUB_Q_JOBID_URL_PATTERN = '%s/jobsub/jobs/jobid/%s/'
JOBSUB_Q_WITH_GROUP_URL_PATTERN = '%s/jobsub/acctgroups/%s/jobs/'
JOBSUB_Q_GROUP_JOBID_URL_PATTERN = '%s/jobsub/acctgroups/%s/jobs/%s/'

JOBSUB_HISTORY_URL_PATTERN = '%s/jobsub/acctgroups/%s/jobs/history/'
#JOBSUB_HISTORY_WITH_USER_PATTERN = '%s/jobsub/acctgroups/%s/jobs/history/%s/'

JOBSUB_HISTORY_WITH_USER_PATTERN = '%s/jobsub/acctgroups/%s/users/%s/jobs/history/'


JOBSUB_ACCTGROUP_HELP_URL_PATTERN = '%s/jobsub/acctgroups/%s/help/'

JOBSUB_CONFIGURED_SITES_URL_PATTERN = '%s/jobsub/acctgroups/%s/sites/'
JOBSUB_JOB_SANDBOX_URL_PATTERN = '%s/jobsub/acctgroups/%s/jobs/%s/sandbox/'
JOBSUB_JOB_LIST_SANDBOXES_URL_PATTERN = '%s/jobsub/acctgroups/%s/sandboxes/%s/'
JOBSUB_JOB_SANDBOX_URL_PATTERN_WITH_ROLE = '%s/jobsub/acctgroups/%s--ROLE--%s/jobs/%s/sandbox/'

JOBSUB_DROPBOX_POST_URL_PATTERN = '%s/jobsub/acctgroups/%s/dropbox/'

JOBSUB_JOB_REMOVE_URL_PATTERN = '%s/jobsub/acctgroups/%s/jobs/%s/'
JOBSUB_JOB_REMOVE_URL_PATTERN_WITH_ROLE = '%s/jobsub/acctgroups/%s--ROLE--%s/jobs/%s/'

JOBSUB_JOB_HOLD_URL_PATTERN = '%s/jobsub/acctgroups/%s/jobs/%s/'
JOBSUB_JOB_HOLD_URL_PATTERN_WITH_ROLE = '%s/jobsub/acctgroups/%s--ROLE--%s/jobs/%s/'

JOBSUB_JOB_RELEASE_URL_PATTERN = '%s/jobsub/acctgroups/%s/jobs/%s/'
JOBSUB_JOB_RELEASE_URL_PATTERN_WITH_ROLE = '%s/jobsub/acctgroups/%s--ROLE--%s/jobs/%s/'

################################################################################
# HTTP/REST API Constants
################################################################################

# HTTP Verbs/Actions
HTTP_GET = 'GET'
HTTP_POST = 'POST'

# Only conside success or failure. Do not translate to actual strings
# 1XX: Informational
# 2XX: Successful
# 3XX: Redirection
# 4XX: Client Error
# 5XX: Server Error
 
HTTP_RESPONSE_CODE_STATUS = {
    200: 'Success',
    201: 'Success',
    203: 'Success',
    204: 'Success',
}

################################################################################
# PyCurl Constants
################################################################################

JOBSUB_PYCURL_CONNECTTIMEOUT = 10
JOBSUB_PYCURL_TIMEOUT = 600
JOBSUB_SSL_VERIFYHOST = 2

################################################################################
# URIs
################################################################################

JOB_EXE_SUPPORTED_URIs = ('file://',)
DROPBOX_SUPPORTED_URI = 'dropbox://'

JOBSUB_SERVER_OPTS_WITH_URI = ('-f',)

JOBSUB_SERVER_OPT_ENV = ('-e','--environment',)

################################################################################
# KRB5 Constants
################################################################################

KRB5TICKET_VALIDITY_HEADER = "Valid starting     Expires            Service principal\\n(.*)\\n.*"

KRB5_DEFAULT_CC = 'FILE:/tmp/krb5cc_%s' % os.getuid()

X509_PROXY_DEFAULT_FILE = '/tmp/jobsub_x509up_u%s' % os.getuid()
