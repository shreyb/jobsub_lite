#!/usr/bin/env python
import os,sys,datetime,string

version_template="""
FILE = version
PRODUCT = jobsub_tools
VERSION = %s

#*************************************************
#
FLAVOR = Linux+2
QUALIFIERS = ""
  DECLARER = products
  DECLARED = 2010-08-26 16.01.33 GMT
  MODIFIER = products
  MODIFIED = 2010-08-26 16.01.33 GMT
  PROD_DIR = jobsub_tools/%s/Linux-2
  UPS_DIR = ups
  TABLE_FILE = %s.table

"""

table_template="""
FILE=TABLE
PRODUCT=jobsub_tools

GROUP:

  FLAVOR=ANY
  QUALIFIERS=""


COMMON:

  ACTION=SETUP
    setupenv()
    proddir()
    envPrepend(JOBSUB_TOOLS5LIB, ${UPS_PROD_DIR}/lib, ':' )
    envPrepend(LD_LIBRARY_PATH, ${UPS_PROD_DIR}/lib/, ':' )
    envPrepend(PYTHONPATH, ${UPS_PROD_DIR}/pylib/, ':' )
    envPrepend(PYTHONPATH, ${UPS_PROD_DIR}/pylib/groupsettings, ':' )
    envPrepend(PYTHONPATH, ${UPS_PROD_DIR}/pylib/JobsubConfigParser, ':' )
    envPrepend(PATH, ${UPS_PROD_DIR}/bin)
    Execute("source ${JOBSUB_TOOLS_DIR}/bin/setup_condor",UPS_ENV)


END:

GROUP:
  FLAVOR=ANY
  QUALIFIERS="build"

COMMON:

  ACTION=SETUP
    envSet(JOBSUB_TOOLS_DIR, ${UPS_PROD_DIR})
    envPrepend(LD_LIBRARY_PATH, ${UPS_PROD_DIR}/lib/, ':' )
    envPrepend(PYTHON_PATH, ${UPS_PROD_DIR}/pylib/, ':' )
    envPrepend(PATH, ${UPS_PROD_DIR}/bin)

END:

"""

current_template="""
FILE = table
PRODUCT = jobsub_tools
CHAIN = current

#*************************************************
#
FLAVOR = Linux+2
VERSION = %s
QUALIFIERS = ""
  DECLARER = products
  DECLARED = 2010-08-26 16.01.33 GMT
  MODIFIER = products
  MODIFIED = 2010-08-26 16.01.33 GMT
"""

if __name__ == "__main__":

    vers=sys.argv[1]
    
    f=open("ups_db/jobsub_tools/%s.table"%vers, 'w')
    f.write(table_template)
    f.close()

    version=version_template % (vers,vers,vers)
    f=open("ups_db/jobsub_tools/%s.version"%vers, 'w')    
    f.write(version)
    f.close()

    current=current_template % (vers)
    f=open("ups_db/jobsub_tools/current.chain", 'w')
    f.write(current)
    f.close()
 
