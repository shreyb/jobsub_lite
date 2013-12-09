import logger
import os
import errno
import zipfile


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


def zipdir(path, zip):
    for root, dirs, files in os.walk(path):
        for file in files:
            zip.write(os.path.join(root, file))


def create_zipfile(zip_file, zip_path):
    zip = zipfile.ZipFile(zip_file, 'w')
    zipdir(zip_path, zip)
    zip.close()


