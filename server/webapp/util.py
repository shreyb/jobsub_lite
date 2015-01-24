import logger
import os
import errno
import zipfile
import tarfile
import time
import sys
import mimetypes
import base64
import json
import hashlib


def encode_multipart_formdata(fields, files, outfile):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    MAINBOUNDARY = 'cbsms-main-boundary'
    SUBBOUNDARY = 'cbsms-sub-boundary'
    CRLF = '\r\n'
    main_content_type = 'multipart/alternative'
    outfile.write('Content-Type: %s; boundary=%s%s' % (main_content_type, MAINBOUNDARY, CRLF))
    outfile.write('--' + MAINBOUNDARY + CRLF)

    sub_content_type = 'multipart/mixed; boundary=%s' % SUBBOUNDARY
    outfile.write('Content-Type: %s%s' % (sub_content_type, CRLF))
    for (key, value) in fields:
        outfile.write('--' + SUBBOUNDARY + CRLF)
        outfile.write('Content-Type: application/json%s' % CRLF)
        outfile.write(CRLF)
        outfile.write(json.dumps(value) + CRLF)
    for (key, filename, value) in files:
        outfile.write('--' + SUBBOUNDARY + CRLF)
        outfile.write('Content-Type: %s; name=%s%s' % (get_content_type(filename), filename, CRLF))
        outfile.write('Content-Location: %s%s' % (filename, CRLF))
        outfile.write('content-transfer-encoding: Base64%s' % CRLF)
        outfile.write(CRLF)
        outfile.write(base64.b64encode(value))
        outfile.write(CRLF)

    outfile.write('--' + SUBBOUNDARY + '--' + CRLF)
    outfile.write('--' + MAINBOUNDARY + '--' + CRLF)
    outfile.write(CRLF)

    return main_content_type


def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


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

def create_tarfile(tar_file, tar_path, job_id=None):
    tar = tarfile.open(tar_file,'w:gz')
    os.chdir(tar_path)
    logger.log('creating tar of %s'%tar_path)
    files=os.listdir(tar_path)
    for file in files:
	f1=os.path.realpath(file)
	f2=os.path.basename(f1)
	tar.add(f1,f2)
    tar.close()

def needs_refresh(filepath,agelimit=3600):
    if not os.path.exists(filepath):
        return True
    if agelimit == sys.maxint:
        return False
    rslt=False
    agelimit=int(agelimit)
    age=sys.maxint
    try:
        st=os.stat(filepath)
        age=(time.time()-st.st_mtime)
    except:
        pass
    if age>agelimit:
        rslt=True
    return rslt


def digest_for_file(fileName, block_size=2**20):
    dig = hashlib.sha1()
    f=open(fileName,'r')
    while True:
        data = f.read(block_size)
        if not data:
            break
        dig.update(data)
    f.close()
    x=dig.hexdigest()
    return x
