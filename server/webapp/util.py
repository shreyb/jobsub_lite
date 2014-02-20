import logger
import os
import errno
import zipfile
import time
import sys


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def get_uid(subject_dn):
    uid = 'unknown'
    try:
        uid = subject_dn.split(':')[1]
    except:
        logger.log('Exception getting uid: ', traceback=True)
    return uid


def zipdir(path, zip, job_id):
    for root, dirs, files in os.walk(path, followlinks=False):
        for file in files:
            if job_id:
                zip.write(os.path.join(root, file), os.path.join(job_id, file))
            else:
                zip.write(os.path.join(root, file))


def create_zipfile(zip_file, zip_path, job_id=None):
    zip = zipfile.ZipFile(zip_file, 'w')
    zipdir(zip_path, zip, job_id)
    zip.close()

def needs_refresh(filepath,agelimit=3600):
    rslt=False
    agelimit=int(agelimit)
    age=sys.maxint
    try:
        if  os.path.exists(filepath):
            st=os.stat(filepath)
            age=(time.time()-st.st_mtime)
    except:
        pass
    if age>agelimit:
        rslt=True
    #logger.log("needs_refresh:file %s age %s limit %s needs_refresh=%s"%(filepath,age,agelimit,rslt))
    return rslt
    
