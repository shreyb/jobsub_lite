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
FILE=table
Product=jobsub_client

Flavor=ANY
QUalifiers=

Action=setup

   setupenv()
   proddir()
   envPrepend(PYTHONPATH, ${UPS_PROD_DIR},':' )
   envPrepend(PATH, ${UPS_PROD_DIR},':' )
   envSet(JOBSUB_CLIENT_DIR, ${UPS_PROD_DIR})

   Execute(python -V 2>&1 , NO_UPS_ENV, PYVER)
   #Execute(echo "before: $PYVER", NO_UPS_ENV)
   If ( expr "$PYVER" : "Python 2.7" > /dev/null )
      Execute(:,NO_UPS_ENV)
   Else()
      #Execute(echo "setting up python", NO_UPS_ENV)
      SourceRequired(`ups setup python v2_7_3`, NO_UPS_ENV)
      EnvSet(JOBSUB_CLIENT_SET_PYTHON,'True')
   EndIf ( expr "$PYVER" : "Python 2.7" > /dev/null )
   If ( expr "$PYTHONPATH" : ".*pycurl" > /dev/null )
      Execute(:,NO_UPS_ENV)
   Else()
      #Execute(echo "setting up pycurl", NO_UPS_ENV)
      SourceRequired(`ups setup pycurl`, NO_UPS_ENV)
      EnvSet(JOBSUB_CLIENT_SET_PYCURL,'True')
   EndIf ( expr "$PYTHONPATH" : ".*pycurl" > /dev/null )
   Execute(python -V 2>&1 , NO_UPS_ENV, PYVER)
   #Execute(echo "after: $PYVER", NO_UPS_ENV)
   EnvUnSet(PYVER)

Action=unsetup
     if( test -n "$JOBSUB_CLIENT_SET_PYTHON" )
       #Execute(echo "unsetting up python", NO_UPS_ENV)
       sourceRequired(`ups unsetup python `, NO_UPS_ENV)
       envUnset(JOBSUB_CLIENT_SET_PYTHON)
     endif( test -n "$JOBSUB_CLIENT_SET_PYTHON" )
     if( test -n "$JOBSUB_CLIENT_SET_PYCURL" )
       #Execute(echo "unsetting up pycurl", NO_UPS_ENV)
       sourceRequired(`ups unsetup pycurl `, NO_UPS_ENV)
       envUnset(JOBSUB_CLIENT_SET_PYCURL)
     endif( test -n "$JOBSUB_CLIENT_SET_PYCURL" )
     pathRemove(PYTHONPATH, ${UPS_PROD_DIR} )
     pathRemove(PATH, ${UPS_PROD_DIR})
     unproddir()
     unsetupenv()


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
 
