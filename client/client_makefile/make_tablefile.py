#!/usr/bin/env python
#file: make_tablefile.py
#purpose: creates ups table and version files for python_future_six_request ups product
#called by: Makefile ups_product_dir target
#author: Dennis Box, dbox@fnal.gov
#
import os
import sys
import datetime
import string
import subprocess

version_template = """
FILE = version
PRODUCT = %s
VERSION = %s

#*************************************************
#
FLAVOR = %s
QUALIFIERS = "%s"
  DECLARER = %s
  DECLARED = %s
  MODIFIER = %s
  MODIFIED = %s
  PROD_DIR = %s/%s/%s
  UPS_DIR = ups
  TABLE_FILE = %s.table

"""

table_template = """

Flavor=%s
Qualifiers=%s

Action=setup

    setupEnv()
    prodDir()
    envPrepend(PYTHONPATH, ${UPS_PROD_DIR},':' )
    setupoptional(curl v7_67_0)

Action=unsetup
    pathRemove(PYTHONPATH, ${UPS_PROD_DIR} )
    unproddir()
    unsetupoptional(curl)
    unsetupenv()


"""


def mk_dir_recursive(dir_path):

    if os.path.isdir(dir_path):
        return
    h, t = os.path.split(dir_path)  # head/tail
    if not os.path.isdir(h):
        mk_dir_recursive(h)

    new_path = os.path.join(h, t)
    if not os.path.isdir(new_path):
        os.mkdir(new_path)

# ./make_tablefile.py ${PRODUCT_NAME} ${PRODUCT_VERSION} ${PYFLAVOR}
if __name__ == "__main__":

    product_name = sys.argv[1]
    vers = sys.argv[2]
    pyflavor = sys.argv[3]
    try:
        upsflavor = subprocess.check_output(['ups', 'flavor']).strip()
    except:
        upsflavor  = subprocess.Popen(['ups', 'flavor'], stdout=subprocess.PIPE).communicate()[0]
        upsflavor = upsflavor.strip()
    try:
        upsflavor = upsflavor.decode('utf-8')
    except:
        pass
    flavor = "%s-%s" % (upsflavor,pyflavor)
    allproducts=os.environ.get('PRODUCTS')
    parts = allproducts.split(':')
    prod_dir = parts[0]

    gmt = datetime.datetime.utcnow()
    dstr = "%s-%s-%s %s.%s.%s GMT" % (gmt.year, gmt.month, gmt.day, gmt.hour,
                                      gmt.minute, gmt.second)
    user = os.environ.get('USER')
    table_file_name = "%s/%s/%s.table" % (prod_dir,product_name,vers)
    table_dir = os.path.dirname(table_file_name)
    mk_dir_recursive(table_dir)
    if not os.path.exists(table_file_name):
        f = open(table_file_name, 'w')
        f.write("File=Table\n")
        f.write("Product=%s\n\n\n" % product_name)
        f.close()

    f = open(table_file_name, 'a')
    f.write(table_template % (upsflavor,pyflavor))
    f.close()
    vfilename = "%s-%s" % (upsflavor,pyflavor)
    #product version, upsflavor, pyflavor,
    version = version_template % (product_name, vers, upsflavor, pyflavor,
              user, dstr, user, dstr, product_name, vers,
              vfilename, vers)
    version_file_name = "%s/%s/%s.version/%s" % (prod_dir,
                                                 product_name,vers,vfilename)
    version_dir = os.path.dirname(version_file_name)
    mk_dir_recursive(version_dir)
    f = open(version_file_name, 'w')
    f.write(version)
    f.close()

