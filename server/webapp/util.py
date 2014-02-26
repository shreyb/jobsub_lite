import logger
import os
import errno
import zipfile
import time
import sys
import mimetypes
import base64


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
        outfile.write(value + CRLF)
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

