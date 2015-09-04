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
import StringIO
import jobsub
import condor_commands 
import re
import cherrypy



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
    logger.log('tar_file=%s tar_path=%s job_id=%s'%(tar_file, tar_path, job_id))
    tar = tarfile.open(tar_file,'w:gz')
    os.chdir(tar_path)
    logger.log('creating tar of %s'%tar_path)
    failed_file_list=[]
    f0 = os.path.realpath(tar_path)
    files=os.listdir(tar_path)
    for file in files:
        f1=os.path.join(f0,file)
        try:
            tar.add(f1,file)
        except:
            logger.log('failed to add %s to %s '%(file,tar_file))
            failed_file_list.append(file)
    if len(failed_file_list)>0:
        failed_fname = "/tmp/%s.MISSING_FILES" % \
            os.path.basename(tar_file)
        f=open(failed_fname,"w")
        f.write("""
                The following files were present in the log directory
                but were not downloaded.  The most likely reason is that 
                condor changed read permissions on individual files as jobs 
                completed.  If you repeat the jobsub_fetchlog command that
                retrieved this tarball  after the jobs that caused the
                problem have completed they will probably download:
                \n"""
                )
        for fname in failed_file_list:
            f.write("%s\n" % fname)
        f.close() 
        tar.add(failed_fname , 
            os.path.basename(failed_fname))
        os.remove(failed_fname)
    tar.close()



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

def condorCommands():
    c = {
        'REMOVE': 'condor_rm',
        'HOLD': 'condor_hold',
        'RELEASE': 'condor_release',
        }
    return c

def doJobAction(acctgroup, job_id=None, user=None, job_action=None, **kwargs):

    scheddList = []
    if job_id:
        #job_id is a jobsubjobid
        constraint = 'regexp("group_%s.*",AccountingGroup)' % (acctgroup)
        # Split the jobid to get cluster_id and proc_id
        stuff=job_id.split('@')
        schedd_name='@'.join(stuff[1:])
        logger.log("schedd_name is %s"%schedd_name)
        scheddList.append(schedd_name)
        ids = stuff[0].split('.')
        constraint = '%s && (ClusterId == %s)' % (constraint, ids[0])
        if (len(ids) > 1) and (ids[1]):
            constraint = '%s && (ProcId == %s)' % (constraint, ids[1])
    elif user:
            constraint = '(Owner =?= "%s") && regexp("group_%s.*",AccountingGroup)' % (user,acctgroup)
            scheddList = condor_commands.schedd_list()
    else:
        err = "Failed to supply job_id or uid, cannot perform any action"
        logger.log(err)
        return err

    logger.log('Performing %s on jobs with constraints (%s)' % (job_action, constraint))

                        
    child_env = os.environ.copy()
    child_env['X509_USER_PROXY'] = cherrypy.request.vomsProxy
    out = err = ''
    affected_jobs = 0
    regex = re.compile('^job_[0-9]+_[0-9]+[ ]*=[ ]*[0-9]+$')
    extra_err = ""
    for schedd_name in scheddList:
        try:
            cmd = [
                jobsub.condor_bin(condorCommands()[job_action]), '-l',
                '-name', schedd_name,
                '-constraint', constraint
            ]
            if job_action == 'REMOVE' and kwargs.get('forcex'):
                cmd.append('-forcex')
            out, err = jobsub.run_cmd_as_user(cmd, cherrypy.request.username, child_env=child_env)
        except:
            #TODO: We need to change the underlying library to return
            #      stderr on failure rather than just raising exception
            #however, as we are iterating over schedds we don't want
            #to return error condition if one fails, we need to 
            #continue and process the other ones
            err="%s: exception:  %s "%(cmd,sys.exc_info()[1])
            logger.log(err,traceback=1)
            extra_err = extra_err + err
            #return {'out':out, 'err':err}
        out = StringIO.StringIO('%s\n' % out.rstrip('\n')).readlines()
        for line in out:
            if regex.match(line):
                affected_jobs += 1
    retStr = "Performed %s on %s jobs matching your request %s" % (job_action, affected_jobs, extra_err)
    return retStr

def doDELETE(acctgroup,  user=None, job_id=None, **kwargs):
    rc = {'out': None, 'err': None}

    rc['out'] = doJobAction(
                        acctgroup,  user=user, 
                        job_id=job_id,
                        job_action='REMOVE', 
                        **kwargs)

    return rc


def doPUT(acctgroup,  user=None,  job_id=None, **kwargs):
    """
    Executed to hold and release jobs
    """

    rc = {'out': None, 'err': None}
    job_action = kwargs.get('job_action')

    if job_action and job_action.upper() in condorCommands():
        rc['out'] = doJobAction(
                            acctgroup,  user=user,
                            job_id=job_id,
                            job_action=job_action.upper())
    else:

        rc['err'] = '%s is not a valid action on jobs' % job_action

    logger.log(rc)

    return rc

