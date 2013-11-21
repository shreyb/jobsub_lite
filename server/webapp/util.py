import logger
import os
import errno


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


