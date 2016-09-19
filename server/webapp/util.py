import logger
import logging
import os
import errno
import zipfile
import tarfile
import sys
import mimetypes
import base64
import json
import hashlib
import StringIO
import jobsub
import condor_commands
import re
import cherrypy
import authutils
import socket


def encode_multipart_formdata(fields, files, outfile):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be
    uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    MAINBOUNDARY = 'cbsms-main-boundary'
    SUBBOUNDARY = 'cbsms-sub-boundary'
    CRLF = '\r\n'
    main_content_type = 'multipart/alternative'
    outfile.write('Content-Type: %s; boundary=%s%s' %
                  (main_content_type, MAINBOUNDARY, CRLF))
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
        outfile.write('Content-Type: %s; name=%s%s' %
                      (get_content_type(filename), filename, CRLF))
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
        logger.log('Exception getting uid: ',
                   traceback=True, severity=logging.ERROR)
        logger.log('Exception getting uid: ',
                   traceback=True,
                   severity=logging.ERROR,
                   logfile='error')
    return uid


def zipdir(path, zip, job_id):
    for root, dirs, files in os.walk(path, followlinks=False):
        for file in files:
            if job_id:
                zip.write(os.path.join(root, file), os.path.join(job_id, file))
            else:
                zip.write(os.path.join(root, file))


def create_zipfile(zip_file, zip_path, job_id=None, partial=None):
    zip = zipfile.ZipFile(zip_file, 'w')
    zipdir(zip_path, zip, job_id)
    zip.close()


def create_tarfile(tar_file, tar_path, job_id=None, partial=None):
    logger.log('tar_file=%s tar_path=%s job_id=%s partial=%s' %
               (tar_file, tar_path, job_id, partial))
    tar = tarfile.open(tar_file, 'w:gz')
    os.chdir(tar_path)
    logger.log('creating tar of %s' % tar_path)
    failed_file_list = []
    f0 = os.path.realpath(tar_path)
    files = os.listdir(tar_path)
    if job_id and partial:
        job_parts = job_id.split('@')
        jnum = job_parts[0]
        logger.log('jnum=%s' % jnum)

    for file in files:
        f1 = os.path.join(f0, file)
        try:
            if partial:
                if jnum in file or partial in file:
                    tar.add(f1, file)
            else:
                tar.add(f1, file)

        except:
            logger.log('failed to add %s to %s ' %
                       (file, tar_file), severity=logging.ERROR)
            logger.log('failed to add %s to %s ' % (file, tar_file),
                       severity=logging.ERROR,
                       logfile='error')
            failed_file_list.append(file)
    if len(failed_file_list) > 0:
        failed_fname = "/tmp/%s.MISSING_FILES" % \
            os.path.basename(tar_file)
        f = open(failed_fname, "w")
        f.write("""
                The following files were present in the log directory
                but were not downloaded.  The most likely reason is that 
                condor changed read permissions on individual files as jobs 
                completed.  If you repeat the jobsub_fetchlog command that
                retrieved this tarball  after the jobs that caused the
                problem have completed they will probably download:
                \n""")

        for fname in failed_file_list:
            f.write("%s\n" % fname)
        f.close()
        tar.add(failed_fname, os.path.basename(failed_fname))
        os.remove(failed_fname)
    tar.close()


def digest_for_file(fileName, block_size=2**20):
    dig = hashlib.sha1()
    f = open(fileName, 'r')
    while True:
        data = f.read(block_size)
        if not data:
            break
        dig.update(data)
    f.close()
    x = dig.hexdigest()
    return x


def condorCommands():
    c = {
        'REMOVE': 'condor_rm',
        'HOLD': 'condor_hold',
        'RELEASE': 'condor_release',
    }
    return c


def doJobAction(acctgroup,
                job_id=None,
                user=None,
                job_action=None,
                constraint=None,
                **kwargs):

    scheddList = []
    rc = {'out': None, 'err': None}
    if constraint:
        scheddList = condor_commands.schedd_list()
    elif job_id:
        # job_id is a jobsubjobid
        constraint = 'regexp("group_%s.*",AccountingGroup)' % (acctgroup)
        # Split the jobid to get cluster_id and proc_id
        stuff = job_id.split('@')
        schedd_name = '@'.join(stuff[1:])
        logger.log("schedd_name is %s" % schedd_name)
        scheddList.append(schedd_name)
        ids = stuff[0].split('.')
        constraint = '%s && (ClusterId == %s)' % (constraint, ids[0])
        if (len(ids) > 1) and (ids[1]):
            constraint = '%s && (ProcId == %s)' % (constraint, ids[1])
    elif user:
        constraint = '(Owner =?= "%s")&&regexp("group_%s.*",AccountingGroup)' %\
            (user, acctgroup)
        scheddList = condor_commands.schedd_list()
    else:
        err = "Failed to supply job_id or uid, cannot perform any action"
        logger.log(err, severity=logging.ERROR)
        logger.log(err, severity=logging.ERROR, logfile='error')
        return {'err': err}

    cmd_user = cherrypy.request.username
    cmd_proxy = cherrypy.request.vomsProxy

    if user and user != cherrypy.request.username and \
            not jobsub.is_superuser_for_group(acctgroup,
                                              cherrypy.request.username):
        err = '%s is not allowed to perform %s on jobs owned by %s ' %\
            (cherrypy.request.username, job_action, user)
        logger.log(err)
        logger.log(err, logfile='condor_superuser')
        logger.log(err, logfile='condor_commands')
        logger.log(err, logfile='error', severity=logging.ERROR)
        return {'err': err}

    if user and user != cherrypy.request.username and \
            jobsub.is_superuser_for_group(acctgroup,
                                          cherrypy.request.username):
        cmd_user = user
        acctrole = 'Analysis'
        if acctgroup in user and 'pro' in user:
            acctrole = 'Production'
        cmd_proxy = authutils.x509_proxy_fname(cmd_user, acctgroup, acctrole)
        logger.log('proxy for %s is %s' % (cmd_user, cmd_proxy))
        msg = '[user: %s] %s jobs owned by %s with constraints (%s) ' %\
            (cherrypy.request.username, job_action, cmd_user, constraint)
        logger.log(msg)
        logger.log(msg, logfile='condor_commands')
        logger.log(msg, logfile='condor_superuser')
    else:
        msg = '[user: %s] %s  jobs with constraint (%s)' %\
            (cherrypy.request.username, job_action, constraint)
        logger.log(msg)
        logger.log(msg, logfile='condor_commands')

    child_env = os.environ.copy()
    child_env['X509_USER_PROXY'] = cmd_proxy
    out = err = ''
    affected_jobs = 0
    expr = '.*(\d+)(\s+Succeeded,\s+)(\d+)(\s+Failed,\s+)*'
    expr2 = '.*ailed to connect*'
    expr3 = '.*all jobs matching constraint*'
    # not needed now but if we ever want them.....
    # expr+='(\d+)(\s+Not\s+Found,\s+)(\d+)(\s+Bad\s+Status,\s+)'
    # expr+='(\d+)(\s+Already\s+Done,\s+)(\d+)(\s+Permission\s+Denied\s+)*'
    regex = re.compile(expr)
    regex2 = re.compile(expr2)
    regex3 = re.compile(expr3)
    extra_err = ""
    failures = 0
    retOut = ""
    retErr = ""

    collector_host = condor_commands.collector_host()
    logger.log('collector_host is "%s"' % collector_host)
    hostname = socket.gethostname()
    for schedd_name in scheddList:
        if hostname in schedd_name:
            try:
                cmd = [
                    jobsub.condor_bin(condorCommands()[job_action]), '-totals',
                    '-name', schedd_name,
                    '-pool', collector_host,
                    '-constraint', constraint
                ]
                if job_action == 'REMOVE' and kwargs.get('forcex'):
                    cmd.append('-forcex')
                out, err = jobsub.run_cmd_as_user(
                    cmd, cmd_user, child_env=child_env)
                extra_err = err
            except:
                # TODO: We need to change the underlying library to return
                #      stderr on failure rather than just raising exception
                # however, as we are iterating over schedds we don't want
                # to return error condition if one fails, we need to
                # continue and process the other ones
                failures += 1
                err = "%s: exception:  %s " % (cmd, sys.exc_info()[1])
                logger.log(err, traceback=1)
                msg = "%s - %s" % (cmd, err)
                logger.log(msg, severity=logging.ERROR)
                logger.log(msg, severity=logging.ERROR,
                           logfile='condor_commands')
                logger.log(msg, severity=logging.ERROR, logfile='error')
                if user and user != cherrypy.request.username:
                    logger.log(msg, severity=logging.ERROR,
                               logfile='condor_superuser')
                extra_err = extra_err + err
                return {'out': out, 'err': extra_err}
            out2 = StringIO.StringIO('%s\n' % out.rstrip('\n')).readlines()
            for line in out2:
                if regex.match(line):
                    grps = regex.match(line)
                    affected_jobs += int(grps.group(1))
                    retOut += line
            err2 = StringIO.StringIO('%s\n' % err.rstrip('\n')).readlines()
            for line in err2:
                if regex.match(line):
                    retOut += line.replace('STDOUT:', '')
                if regex2.match(line):
                    retErr += line
                if regex3.match(line):
                    retErr += line
    #retOut += "Performed %s on %s jobs matching your request %s" % (job_action, affected_jobs, extra_err)
    # if failures:
    #    retOut = "%s \nCONDOR_ERRORS: %s" %( retOut, extra_err )
    if err and not retErr:
        retErr = err
    return {'out': retOut, 'err': retErr}


def doDELETE(acctgroup,  user=None, job_id=None, constraint=None, **kwargs):

    rc = doJobAction(
        acctgroup,  user=user, constraint=constraint,
        job_id=job_id,
        job_action='REMOVE',
        **kwargs)

    return rc


def doPUT(acctgroup,  user=None,  job_id=None, constraint=None, **kwargs):
    """
    Executed to hold and release jobs
    """

    rc = {'out': None, 'err': None}
    job_action = kwargs.get('job_action')

    if job_action and job_action.upper() in condorCommands():
        rc = doJobAction(
            acctgroup,  user=user, constraint=constraint,
            job_id=job_id,
            job_action=job_action.upper())
    else:

        rc['err'] = '%s is not a valid action on jobs' % job_action

    logger.log(rc)

    return rc
