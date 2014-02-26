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

# Default JobSub Server
JOBSUB_SERVER = 'https://jobsub.fnal.gov'

# Default JobSub job submission url pattern
# https://server.com/jobsub/api/<api-version>/accountinggroups/<exp-name>/jobs

#JOBSUB_JOB_SUBMIT_URL_PATTERN = '%s/jobsub/api/%s/acctgroups/%s/jobs'
JOBSUB_JOB_SUBMIT_URL_PATTERN = '%s/jobsub/acctgroups/%s/jobs/'
JOBSUB_JOB_SUBMIT_URL_PATTERN_WITH_ROLE = '%s/jobsub/acctgroups/%s--ROLE--%s/jobs/'

JOBSUB_ACCTGROUP_HELP_URL_PATTERN = '%s/jobsub/acctgroups/%s/help/'

JOBSUB_JOB_SANDBOX_URL_PATTERN = '%s/jobsub/acctgroups/%s/jobs/%s/sandbox/'
JOBSUB_JOB_SANDBOX_URL_PATTERN_WITH_ROLE = '%s/jobsub/acctgroups/%s--ROLE--%s/jobs/%s/sandbox/'

JOBSUB_DROPBOX_POST_URL_PATTERN = '%s/jobsub/acctgroups/%s/dropbox/'

################################################################################
# HTTP/REST API Constants
################################################################################

# HTTP Verbs/Actions
HTTP_GET = 'GET'
HTTP_POST = 'POST'

################################################################################
# PyCurl Constants
################################################################################

JOBSUB_PYCURL_CONNECTTIMEOUT = 5
JOBSUB_PYCURL_TIMEOUT = 30
JOBSUB_SSL_VERIFYHOST = 2

################################################################################
# URIs
################################################################################

JOB_EXE_SUPPORTED_URIs = ('file://',)
DROPBOX_SUPPORTED_URI = 'dropbox://'

JOBSUB_SERVER_OPTS_WITH_URI = ('-f',)

JOBSUB_SERVER_OPT_ENV = ('-e',)

################################################################################
# KRB5 Constants
################################################################################

KRB5TICKET_VALIDITY_HEADER = "Valid starting     Expires            Service principal\\n(.*)\\n.*"

KRB5_DEFAULT_CC = 'FILE:/tmp/krb5cc_%s' % os.getuid()

X509_PROXY_DEFAULT_FILE = '/tmp/x509up_u%s' % os.getuid()
