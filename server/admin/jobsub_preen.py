#! /usr/bin/env python
import subprocessSupport
import logger
import logging
import os
import time
import sys
import shutil


def queuedList():
    dirname = ""
    queuedlist = []
    cmd = "condor_q -format '%s\n' iwd  -format '%s \n' jobsubjobid"
    queued, cmd_err = subprocessSupport.iexe_cmd(cmd)
    for q in queued.split('\n'):
        p = os.path.dirname(q)
        f = os.path.basename(q)
        if f != q:
            dirname = p
            q2 = q
        else:
            if f != "":
                q2 = os.path.join(dirname, f).strip()
            else:
                q2 = ""
        if q2 not in queuedlist and os.path.lexists(q2):
            queuedlist.append(q2)
    logger.log('these directories are in the queue:%s' % queuedlist)
    return queuedlist


def transInputList():
    queuedlist = []
    cmd = """condor_q -af transferinput -constraint """
    cmd += """ 'regexp(".*dropbox.*",TransferInput)' """
    queued, cmd_err = subprocessSupport.iexe_cmd(cmd)
    for q in queued.split('\n'):
        for f in q.split(','):
            d = os.path.dirname(f)
            if 'dropbox' in d and d not in queuedlist:
                queuedlist.append(d)
    logger.log('these directories are in the queue:%s' % queuedlist)
    return queuedlist


def findDirs(rootDir):
    # print 'checking %s'%rootDir
    dirlist = []
    for f in os.listdir(rootDir):
        # print 'checking %s' %f
        f2 = os.path.join(rootDir, f)
        if os.path.isdir(f2):
            dirlist.append(f2)
    return dirlist


def findRmUserJobDirs(rootDir, ageInDays):
    if 'dropbox' in rootDir:
        ql = transInputList()
    else:
        ql = queuedList()
    ageInSeconds = int(ageInDays) * 24 * 60 * 60
    now = time.time()
    userDirs = []
    experimentGroups = findDirs(rootDir)
    for e in experimentGroups:
        userDirs.extend(findDirs(e))
    for udir in userDirs:
        fileList = os.listdir(udir)
        for f in fileList:
            fname = os.path.join(udir, f)
            if os.path.islink(fname) and \
                    not os.path.exists(fname):
                logger.log('removing link %s' % fname)
                try:
                    os.unlink(fname)
                except:
                    logger.log("%s" % sys.exc_info()[1])

            if os.path.exists(fname) and \
                    os.stat(fname).st_mtime < now - ageInSeconds:

                if fname in ql:
                    msg = '%s older than %s days ' % (fname, ageInDays)
                    msg += 'but still in queue - ignoring'
                    logger.log(msg)
                elif os.path.islink(fname):
                    logger.log('removing link %s' % fname)
                    try:
                        os.unlink(fname)
                    except:
                        logger.log("%s" % sys.exc_info()[1])
                else:
                    logger.log('removing directory %s' % fname)
                    try:
                        shutil.rmtree(fname, ignore_errors=True)
                    except:
                        logger.log("%s" % sys.exc_info()[1])


def rmOldFiles(rootDir, ageInDays, doSubDirs=0, rmEmptyDirs=False):
    #doSubDirs now contains depth information, recursively
    #go into subdirs until doSubdirs==0
    #if negative, recurse to bottom
    ageInSeconds = int(ageInDays) * 24 * 60 * 60
    now = time.time()
    if rmEmptyDirs:
        removeEmptyDirs(rootDir)
    fileList = os.listdir(rootDir)
    for f in fileList:
        fname = os.path.join(rootDir, f)
        if os.path.isdir(fname):
            if doSubDirs:
                rmOldFiles(fname, ageInDays, doSubDirs-1, rmEmptyDirs)
        else:
            if os.stat(fname).st_mtime < now - ageInSeconds:

                logger.log('removing file %s' % fname)
                try:
                    os.unlink(fname)
                except:
                    logger.log("%s" % sys.exc_info()[1])


def removeEmptyDirs(rootDir):
    fileList = os.listdir(rootDir)
    for f in fileList:
        fname = os.path.join(rootDir, f)
        if os.path.isdir(fname):
            if len(os.listdir(fname)) == 0:
                try:
                    logger.log('removing empty directory  %s' % fname)
                    os.rmdir(fname)
                except:
                    logger.log("%s" % sys.exc_info()[1])


def print_help():
    help = """
        usage: %s <root_dir> ageInDays [thisDirOnly||doSubDirs||rmEmptySubdirs]

        if arg 3 is 'thisDirOnly':
           remove all files in <root_dir> older than <ageInDays>
        elif arg 3 is 'doSubDirs':
           if arg 4 exists an is an integer:
               remove files in <root_dir> and subdirs older than <ageInDays> down to depth 'arg 4' subdirs
           else:      
              remove all files in <root_dir> and subdirs older than <ageInDays>
        elif arg 3 is 'rmEmptySubdirs':
           remove all files in <root_dir> and subdirs older than <ageInDays>,
           also remove any empty subdirectories
        else:
          remove condor working directories under <root_dir> that are
          older that <ageInDays> .  Will not remove if job associated with
          working directory is still in queue.  Actions are logged to
          $JOBSUB_LOG_DIR/jobsub_preen.log
    """ % sys.argv[0]
    print help


def run_prog():
    if len(sys.argv) == 3:
        findRmUserJobDirs(sys.argv[1], sys.argv[2])
    elif len(sys.argv) >= 4:
        if sys.argv[3] == 'thisDirOnly':
            rmOldFiles(sys.argv[1], sys.argv[2])
        elif sys.argv[3] == 'doSubDirs':
            if len(sys.argv)>=5  and isinstance(int(sys.argv[4]),(int,long)):
            	rmOldFiles(sys.argv[1], sys.argv[2], doSubDirs=int(sys.argv[4]))
            else:
            	rmOldFiles(sys.argv[1], sys.argv[2], doSubDirs=-1)
        elif sys.argv[3] == 'rmEmptySubdirs':
            rmOldFiles(sys.argv[1], sys.argv[2], doSubDirs=True,
                       rmEmptyDirs=True)
        else:
            err = "ERROR arg 3 == '%s' not recognized. A typo?" % sys.argv[3]
            print_help()
            print err
    else:
        print_help()


if __name__ == '__main__':
    try:
        run_prog()
    except:

        logger.log("%s" % sys.exc_info()[1],
                   severity=logging.ERROR,
                   traceback=True)

        logger.log("%s" % sys.exc_info()[1],
                   severity=logging.ERROR,
                   traceback=True,
                   logfile="error")
