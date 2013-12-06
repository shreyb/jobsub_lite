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

################################################################################
# JOBSUB Constants
################################################################################

# Default JobSub Server
JOBSUB_SERVER = 'https://jobsub.fnal.gov'

# Default JobSub job submission url pattern
# https://server.com/jobsub/api/<api-version>/accountinggroups/<exp-name>/jobs

#JOBSUB_JOB_SUBMIT_URL_PATTERN = '%s/jobsub/api/%s/acctgroups/%s/jobs'
JOBSUB_JOB_SUBMIT_URL_PATTERN = '%s/jobsub/acctgroups/%s/jobs/'

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

################################################################################
# URIs
################################################################################

JOB_EXE_SUPPORTED_URIs = ('file://',)

JOBSUB_SERVER_OPTS_WITH_URI = ('-f',)

################################################################################
# STANDARD PATTERNS FOR REGEX
################################################################################

KRB5TICKET_VALIDITY_HEADER = 'Valid starting     Expires            Service principal\n(.*)\n.*'
