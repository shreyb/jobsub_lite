#!/usr/bin/env python
import os,sys,datetime,string

version_template="""
FILE = version
PRODUCT = jobsub_client
VERSION = %s

#*************************************************
#
FLAVOR = NULL
QUALIFIERS = ""
  DECLARER = products
  DECLARED = 2010-08-26 16.01.33 GMT
  MODIFIER = products
  MODIFIED = 2010-08-26 16.01.33 GMT
  PROD_DIR = jobsub_client/%s/NULL
  UPS_DIR = ups
  TABLE_FILE = %s.table

"""

table_template="""
FILE=TABLE
PRODUCT=jobsub_client

GROUP:

  FLAVOR=ANY
  QUALIFIERS=""


COMMON:

  ACTION=SETUP
    setupenv()
    proddir()
    setupRequired(python v2_7_3)
    setupRequired(pycurl )
    envPrepend(PYTHONPATH, ${UPS_PROD_DIR} )
    envPrepend(PATH, ${UPS_PROD_DIR})


END:

GROUP:
  FLAVOR=ANY
  QUALIFIERS="build"

COMMON:

  ACTION=SETUP
    envSet(JOBSUB_TOOLS_DIR, ${UPS_PROD_DIR})
    envPrepend(LD_LIBRARY_PATH, ${UPS_PROD_DIR}/lib/, ':' )
    envPrepend(PYTHONPATH, ${UPS_PROD_DIR}, ':' )
    envPrepend(PATH, ${UPS_PROD_DIR})

END:

"""

current_template="""
FILE = chain
PRODUCT = jobsub_client
CHAIN = current

#*************************************************
#
FLAVOR = NULL
VERSION = %s
QUALIFIERS = ""
  DECLARER = products
  DECLARED = 2010-08-26 16.01.33 GMT
  MODIFIER = products
  MODIFIED = 2010-08-26 16.01.33 GMT
"""

if __name__ == "__main__":

    vers=sys.argv[1]
    
    f=open("ups_db/jobsub_client/%s.table"%vers, 'w')
    f.write(table_template)
    f.close()

    version=version_template % (vers,vers,vers)
    f=open("ups_db/jobsub_client/%s.version"%vers, 'w')    
    f.write(version)
    f.close()

    current=current_template % (vers)
    f=open("ups_db/jobsub_client/current.chain", 'w')
    f.write(current)
    f.close()
 
