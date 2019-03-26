"""
 Description:
   This module contains various utility functions for html encoding
   creating tar and zip files and the like
   Also implements the guts of hold, release, remove queued jobs

 Project:
   JobSub

 Author:
   Nick Palumbo


"""
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
import pwd
import jobsub
import condor_commands
import re
import cherrypy
import authutils
import socket
import request_headers


def encode_multipart_formdata(fields, files, outfile):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, fnameame, value) elements for data to be
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
    for (key, fnameame, value) in files:
        outfile.write('--' + SUBBOUNDARY + CRLF)
        outfile.write('Content-Type: %s; name=%s%s' %
                      (get_content_type(fnameame), fnameame, CRLF))
        outfile.write('Content-Location: %s%s' % (fnameame, CRLF))
        outfile.write('content-transfer-encoding: Base64%s' % CRLF)
        outfile.write(CRLF)
        outfile.write(base64.b64encode(value))
        outfile.write(CRLF)

    outfile.write('--' + SUBBOUNDARY + '--' + CRLF)
    outfile.write('--' + MAINBOUNDARY + '--' + CRLF)
    outfile.write(CRLF)

    return main_content_type


def get_content_type(fnameame):
    """
    guess content type of fnameame
    """
    return mimetypes.guess_type(fnameame)[0] or 'application/octet-stream'


def mkdir_p(path):
    """
    mkdir -p
    """
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def zipdir(path, zipf, job_id):
    """ fill a zipfile from a directory
    @zipf : a previously created zipfile object
    @job_id: a directory of condor log files and job output
    """
    for root, dirs, files in os.walk(path, followlinks=False):
        for fil in files:
            if job_id:
                zipf.write(os.path.join(root, fil),
                           os.path.join(job_id, fil))
            else:
                zipf.write(os.path.join(root, fil))


def create_zipfile(zip_file, zip_path, job_id=None, partial=None):
    """create and fill a zipfile
    @zip_file: name of the zipfile to create
    @zip_path: directory path to the job_id directory containing job information
    @job_id: directory named after jobsub_job_id containing job output and
             condor logs
    """
    zipf = zipfile.ZipFile(zip_file, 'w')
    zipdir(zip_path, zipf, job_id)
    zipf.close()


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

    for fname in files:
        f1 = os.path.join(f0, fname)
        try:
            if partial:
                if jnum in fname or partial in fname:
                    tar.add(f1, fname)
            else:
                tar.add(f1, fname)

        except BaseException:
            logger.log('failed to add %s to %s ' %
                       (fname, tar_file), severity=logging.ERROR)
            logger.log('failed to add %s to %s ' % (fname, tar_file),
                       severity=logging.ERROR,
                       logfile='error')
            failed_file_list.append(fname)
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
    """ calculate and return a sha1 hash for file named
    @fileName
    """

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
        'ADJUST_PRIO': 'condor_prio',
    }
    return c


def doJobAction(acctgroup,
                job_id=None,
                user=None,
                job_action=None,
                constraint=None,
                **kwargs):
    """
    perform a job_action = [HOLD, RELEASE, 'ADJUST_PRIO' or REMOVE]
    subject to constraint = (constraint) or
               constraint = (constructed from user, jobid, acctgroup)
    """
    out = ''
    err = ''
    r_code = {'out': out, 'err': err, 'status': 'starting', 'acctgroup': acctgroup,
              'user': user, 'job_id': job_id, 'constraint': constraint,
              'job_action': job_action, 'kwargs': kwargs}
    if jobsub.log_verbose():
        logger.log(r_code)
    scheddList = []
    try:
        cmd_user = cherrypy.request.username
    except BaseException:
        cmd_user = request_headers.uid_from_client_dn()
    orig_user = cmd_user
    acctrole = kwargs.get('role',
                          jobsub.default_voms_role(acctgroup))
    child_env = os.environ.copy()
    is_group_superuser = jobsub.is_superuser_for_group(acctgroup, cmd_user)
    is_global_superuser = jobsub.is_global_superuser(cmd_user)
    if is_group_superuser or is_global_superuser:
        cmd_user = pwd.getpwuid(os.getuid())[0]
        child_env['X509_USER_CERT'] = child_env['JOBSUB_SERVER_X509_CERT']
        child_env['X509_USER_KEY'] = child_env['JOBSUB_SERVER_X509_KEY']
        msg = "user %s will perform %s  as queue_superuser %s" %\
            (orig_user, job_action, cmd_user)
        r_code['status'] = msg
        logger.log(r_code)

    else:
        cmd_proxy = kwargs.get('voms_proxy',
                               authutils.x509_proxy_fname(cmd_user,
                                                          acctgroup,
                                                          acctrole))
        child_env['X509_USER_PROXY'] = cmd_proxy

    cgroup = """regexp("group_%s.*",AccountingGroup)""" % acctgroup

    if constraint:
        scheddList = condor_commands.schedd_list(acctgroup)

        if user and user not in constraint:
            constraint = """(Owner =?= "%s") && %s""" % (user, constraint)
        if not is_global_superuser:
            if acctgroup not in constraint:
                constraint = """%s && %s""" % (cgroup, constraint)
    elif job_id:
        if is_global_superuser:
            constraint = 'True'
        else:
            constraint = cgroup
        # job_id is a jobsubjobid
        # Split the job_id to get cluster_id and proc_id
        stuff = job_id.split('@')
        schedd_name = '@'.join(stuff[1:])
        r_code['status'] = "schedd_name is %s" % schedd_name
        logger.log(r_code)
        scheddList.append(schedd_name)
        ids = stuff[0].split('.')
        constraint = '%s && (ClusterId == %s)' % (constraint, ids[0])
        if (len(ids) > 1) and (ids[1]):
            constraint = '%s && (ProcId == %s)' % (constraint, ids[1])
    elif user:
        if is_global_superuser:
            constraint = 'True'
        else:
            constraint = cgroup

        constraint = """%s && (Owner =?= "%s")""" % (constraint, user)
        scheddList = condor_commands.schedd_list(acctgroup)
    else:
        err = "Failed to supply constraint, job_id or uid, "
        err += "cannot perform any action"
        r_code['err'] = err
        r_code['status'] = 'error_exit'
        logger.log(r_code, severity=logging.ERROR)
        logger.log(r_code, severity=logging.ERROR, logfile='error')
        return r_code

    if is_group_superuser or is_global_superuser:
        msg = '[user: %s su %s] %s jobs owned by %s with constraint(%s)' %\
            (orig_user, cmd_user, job_action, user, constraint)
        r_code['status'] = msg
        logger.log(r_code)
        logger.log(r_code, logfile='condor_commands')
        logger.log(r_code, logfile='condor_superuser')

    if user and user != cmd_user and not (is_group_superuser or
                                          is_global_superuser):

        r_code['err'] = '%s is not allowed to perform %s on jobs owned by %s ' %\
            (cmd_user, job_action, user)
        r_code['status'] = 'exit_error'
        logger.log(r_code)
        logger.log(r_code, logfile='condor_superuser')
        logger.log(r_code, logfile='condor_commands')
        logger.log(r_code, logfile='error', severity=logging.ERROR)
        return r_code

    else:
        if is_group_superuser:
            if constraint and (acctgroup not in constraint):
                c_and = """&&(regexp("group_%s.*",AccountingGroup))""" %\
                        acctgroup
                constraint = constraint + c_and
        r_code['status'] = '[user: %s] %s  jobs with constraint (%s)' %\
            (cmd_user, job_action, constraint)
        logger.log(r_code)
        logger.log(r_code, logfile='condor_commands')

    out = err = ''
    expr = r'.*(\d+)(\s+Succeeded,\s+)(\d+)(\s+Failed,\s+).*'
    expr += r'(\s+)(\d+)(\s+Permission Denied).*'
    expr2 = '.*ailed to connect*'
    expr3 = '.*all jobs matching constraint*'
    regex = re.compile(expr)
    regex2 = re.compile(expr2)
    regex3 = re.compile(expr3)
    extra_err = ""
    failures = 0
    ret_out = ""
    ret_err = ""

    collector_host = condor_commands.collector_host()
    r_code['status'] = 'collector_host is "%s"' % collector_host
    logger.log(r_code)
    hostname = socket.gethostname()
    for schedd_name in scheddList:
        if hostname in schedd_name:
            cmd = []
            try:
                if job_action == 'ADJUST_PRIO':
                    priority = kwargs.get('prio')
                    if job_id:
                        act_on = job_id.split('@')[0]
                    elif user:
                        act_on = user
                    if not priority:
                        raise RuntimeError(
                            'tried to do jobsub_prio but did not supply a priority')
                    if not (user or job_id):
                        raise RuntimeError(
                            'must supply a user or job_id to jobsub_prio')

                    cmd = [
                        jobsub.condor_bin(condorCommands()[job_action]),
                        '-n', schedd_name,
                        '-pool', collector_host,
                        '-p', priority,
                        act_on
                    ]
                else:
                    cmd = [
                        jobsub.condor_bin(
                            condorCommands()[job_action]), '-totals',
                        '-name', schedd_name,
                        '-pool', collector_host,
                        '-constraint', constraint
                    ]
                if job_action == 'REMOVE' and kwargs.get('forcex'):
                    cmd.append('-forcex')
                if jobsub.log_verbose():
                    logger.log('cmd=%s' % cmd)
                r_code['status'] = "executing %s as %s" % (cmd, cmd_user)
                logger.log(r_code)
                out, err = jobsub.run_cmd_as_user(cmd,
                                                  cmd_user,
                                                  child_env=child_env)
                r_code['status'] = "returned from  %s as %s" % (cmd, cmd_user)
                if out:
                    r_code['out'] = out
                if err:
                    r_code['err'] = err
                extra_err = err
                if jobsub.log_verbose():
                    logger.log(r_code)
            except BaseException:
                # TODO: We need to change the underlying library to return
                #      stderr on failure rather than just raising exception
                # however, as we are iterating over schedds we don't want
                # to return error condition if one fails, we need to
                # continue and process the other ones
                failures += 1
                err = "%s: exception:  %s " % (cmd, sys.exc_info()[1])
                r_code['err'] = err
                logger.log(r_code, traceback=True)
                logger.log(r_code, severity=logging.ERROR)
                logger.log(r_code, severity=logging.ERROR,
                           logfile='condor_commands')
                logger.log(r_code, severity=logging.ERROR, logfile='error')
                if user and user != cmd_user:
                    logger.log(r_code, severity=logging.ERROR,
                               logfile='condor_superuser')
                extra_err = extra_err + err
                # return {'out': out, 'err': extra_err}
            out2 = StringIO.StringIO('%s\n' % out.rstrip('\n')).readlines()
            for line in out2:
                if regex.match(line):
                    ret_out += line
            err2 = StringIO.StringIO('%s\n' % err.rstrip('\n')).readlines()
            for line in err2:
                if regex.match(line):
                    ret_out += line.replace('STDOUT:', '')
                    grps = regex.match(line)
                    fmt = 'condor_stdout=%s succeeded=%s failed=%s denied=%s'
                    logger.log(fmt % (grps.group(),
                                      grps.group(1),
                                      grps.group(3),
                                      grps.group(6)))
                    if grps.group(1) == '0':
                        # 0 Succeeded, return error
                        cherrypy.response.status = 500
                    if grps.group(3) != '0':
                        # non-0 Failed, return error
                        cherrypy.response.status = 500
                    if grps.group(6) != '0':
                        # non-0 Permission Denied, return error
                        cherrypy.response.status = 500
                if regex2.match(line):
                    ret_err += line
                if regex3.match(line):
                    ret_err += line
    if err and not ret_err:
        ret_err = err
    r_code['out'] = ret_out
    r_code['err'] = ret_err
    r_code['status'] = 'exiting'
    return r_code


def doDELETE(acctgroup, user=None, job_id=None, constraint=None, **kwargs):
    """
    Executed to remove jobs
    """

    r_code = doJobAction(acctgroup,
                         user=user,
                         constraint=constraint,
                         job_id=job_id,
                         job_action='REMOVE',
                         **kwargs)

    return r_code


def doPUT(acctgroup, user=None, job_id=None, constraint=None, **kwargs):
    """
    Executed to hold,release, or adust job priority

    """
    out = ''
    err = ''
    r_code = {'out': out, 'err': err, 'status': 'starting', 'acctgroup': acctgroup,
              'user': user, 'job_id': job_id, 'constraint': constraint, 'kwargs': kwargs}
    if jobsub.log_verbose():
        logger.log(r_code)
    job_action = kwargs.get('job_action')
    if job_action:
        job_action = job_action.upper()
        if job_action == 'ADJUST_PRIO' and constraint:
            err = "something went wrong, constraints not allowed for"
            err += " command jobsub_prio "
            r_code['err'] = err
            r_code['status'] = 'error'
    else:
        err = 'must supply a job action'
        r_code['err'] = err
        r_code['status'] = 'error'

    if not r_code['err']:
        if job_action in condorCommands():
            del kwargs['job_action']
            r_code['status'] = 'calling doJobAction'
            r_code2 = doJobAction(acctgroup,
                                  user=user,
                                  constraint=constraint,
                                  job_id=job_id,
                                  job_action=job_action.upper(),
                                  **kwargs)
            if r_code2.get('out'):
                r_code['out'] = r_code2['out']
            if r_code2.get('err'):
                r_code['err'] = r_code2['err']
            if jobsub.log_verbose():
                logger.log(r_code)
        else:
            r_code['err'] = '%s is not a valid action on jobs' % job_action

    if r_code['err']:
        r_code['status'] = 'exit_failure'
    else:
        r_code['status'] = 'exit_success'
    if jobsub.log_verbose():
        logger.log(r_code)

    return r_code
