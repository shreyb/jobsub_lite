#!/usr/bin/env python
import os
import sys
import datetime
import string

version_template = """
FILE = version
PRODUCT = jobsub_client
VERSION = %s

#*************************************************
#
FLAVOR = NULL
QUALIFIERS = ""
  DECLARER = %s
  DECLARED = %s
  MODIFIER = %s
  MODIFIED = %s
  PROD_DIR = jobsub_client/%s/NULL
  UPS_DIR = ups
  TABLE_FILE = %s.table

"""

table_template = """


FILE=table
Product=jobsub_client

Flavor=ANY
QUalifiers=

Action=setup

    setupEnv()
    prodDir()
    envPrepend(PYTHONPATH, ${UPS_PROD_DIR},':' )
    envPrepend(PATH, ${UPS_PROD_DIR},':' )
    #envSet(JOBSUB_CLIENT_DIR, ${UPS_PROD_DIR})

    setupRequired(cigetcert)
    setupRequired(ifdhc)
    Execute( "which python "  , NO_UPS_ENV, JOBSUB_PYVER )
    If( test "$JOBSUB_PYVER" != "/usr/bin/python" )
           Execute( "ups setup pycurl",  NO_UPS_ENV, JOBSUB_PYCURL_SET_SOURCE )
           sourceRequired("$JOBSUB_PYCURL_SET_SOURCE", NO_UPS_ENV )
           envUnSet(JOBSUB_PYCURL_SET_SOURCE)
    EndIf( test "$JOBSUB_PYVER" != "/usr/bin/python" )

Action=unsetup
    If( test "$PYCURL_DIR" != "" )
       Execute( "ups unsetup pycurl",  NO_UPS_ENV, JOBSUB_PYCURL_UNSET_SOURCE )
       sourceRequired("$JOBSUB_PYCURL_UNSET_SOURCE" , NO_UPS_ENV )
       envUnSet(JOBSUB_PYCURL_UNSET_SOURCE)
    EndIf( test "$PYCURL_DIR" != "" )
    pathRemove(PYTHONPATH, ${UPS_PROD_DIR} )
    pathRemove(PATH, ${UPS_PROD_DIR})
    envUnSet(JOBSUB_PYVER)
         
    unproddir()
    unsetupenv()
              

"""

current_template = """
FILE = chain
PRODUCT = jobsub_client
CHAIN = current

#*************************************************
#
FLAVOR = NULL
VERSION = %s
QUALIFIERS = ""
  DECLARER = %s
  DECLARED = %s
  MODIFIER = %s
  MODIFIED = %s
"""

if __name__ == "__main__":

    vers = sys.argv[1]
    gmt = datetime.datetime.utcnow()
    dstr = "%s-%s-%s %s.%s.%s GMT" % (gmt.year, gmt.month, gmt.day, gmt.hour,
                                      gmt.minute, gmt.second)
    user = os.environ.get('USER')
    f = open("ups_db/jobsub_client/%s.table" % vers, 'w')
    f.write(table_template)
    f.close()

    version = version_template % (vers, user, dstr, user, dstr, vers, vers)
    f = open("ups_db/jobsub_client/%s.version" % vers, 'w')
    f.write(version)
    f.close()

    current = current_template % (vers, user, dstr, user, dstr)
    f = open("ups_db/jobsub_client/current.chain", 'w')
    f.write(current)
    f.close()
