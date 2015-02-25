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
   Execute( "grep ' 5\.' /etc/redhat-release " , NO_UPS_ENV, IS_SL5 )
   envSetIfNotSet(IS_SL5,"ItsNotSL5") 
   If( test "$IS_SL5" = "" )
      envSet( IS_SL5, "ItsNotSL5")
   EndIf( test "$IS_SL5" = "" )
   If( test "$IS_SL5" != "ItsNotSL5" )
       #Execute( echo "its sl5, testing if python set up" , NO_UPS_ENV )
       Execute( "which python "  , NO_UPS_ENV, PYVER)
       If( test "$PYVER" != "/usr/bin/python" )
          Execute(:, NO_UPS_ENV )
       Else()
          #Execute( echo "setting up python" , NO_UPS_ENV )
          SourceRequired(`ups setup python v2_7_3`, NO_UPS_ENV )
          EnvSet(JOBSUB_CLIENT_SET_PYTHON,'True')
       EndIf( test "$PYVER" != "/usr/bin/python" )
       If( expr "$PYTHONPATH" : ".*pycurl" > /dev/null )
          Execute(:, NO_UPS_ENV )
       Else()
          #Execute( echo "setting up pycurl" , NO_UPS_ENV )
          SourceRequired(`ups setup pycurl`, NO_UPS_ENV )
          EnvSet(JOBSUB_CLIENT_SET_PYCURL,'True')
       EndIf( expr "$PYTHONPATH" : ".*pycurl" > /dev/null )
       EnvUnSet(PYVER)
   Else()
       #Execute( echo "its sl6, testing if python set up" , NO_UPS_ENV )
       Execute( "which python "  , NO_UPS_ENV, PYVER)
       If( test "$PYVER" != "/usr/bin/python" )
          #Execute( echo "python set up, testing for pycurl" , NO_UPS_ENV )
          If( expr "$PYTHONPATH" : ".*pycurl" > /dev/null )
             Execute(:, NO_UPS_ENV )
          Else()
             #Execute( echo "setting up pycurl" , NO_UPS_ENV )
             SourceRequired(`ups setup pycurl`, NO_UPS_ENV )
             EnvSet(JOBSUB_CLIENT_SET_PYCURL,'True')
          EndIf( expr "$PYTHONPATH" : ".*pycurl" > /dev/null )
       Else()
          Execute(:, NO_UPS_ENV )
          #Execute( echo "python not set up, doing nothing" , NO_UPS_ENV )
       EndIf( test "$PYVER" != "/usr/bin/python" )
   EndIf( test "$IS_SL5" != "ItsNotSL5" )

Action=unsetup
     envSetIfNotSet(JOBSUB_CLIENT_SET_PYTHON,"False") 
    If( test "$JOBSUB_CLIENT_SET_PYTHON" = "True" )
       #Execute( echo "unsetting up python" , NO_UPS_ENV )
       sourceRequired( `ups unsetup python `, NO_UPS_ENV )
     EndIf( test "$JOBSUB_CLIENT_SET_PYTHON" = "True" )
     envSetIfNotSet(JOBSUB_CLIENT_SET_PYCURL,"False") 
    If( test "$JOBSUB_CLIENT_SET_PYCURL" = "True")
       #Execute( echo "unsetting up pycurl" , NO_UPS_ENV )
       sourceRequired( `ups unsetup pycurl `, NO_UPS_ENV )
     EndIf( test "$JOBSUB_CLIENT_SET_PYCURL" = "True")
     pathRemove(PYTHONPATH, ${UPS_PROD_DIR} )
     pathRemove(PATH, ${UPS_PROD_DIR})
     envUnSet(JOBSUB_CLIENT_SET_PYTHON)
     envUnSet(JOBSUB_CLIENT_SET_PYCURL)
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
 
