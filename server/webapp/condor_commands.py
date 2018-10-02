"""file: condor_commands.py
    Purpose:
        utility file with implementation of various condor commands such as
        condor_q, condor_status, etc
        no actual api implemented in this module

    Project:
        Jobsub

    Author:
        Dennis Box
"""
import os
import cherrypy
import logging
import traceback
import math
import platform
import socket
import re
from random import randint

import JobsubConfigParser
import subprocessSupport
from request_headers import get_client_dn

if os.getenv('JOBSUB_USE_FAKE_LOGGER'):
    import FakeLogger as logger
else:
    import logger


JOBSTATUS_DICT = {'unexpanded': 0, 'idle': 1, 'run': 2, 'running': 2,
                  'removed': 3, 'completed': 4, 'held': 5, 'hold': 5,
                  'error': 6}
if platform.system() == 'Linux':
    try:
        import htcondor as condor
    except ImportError:
        logger.log('Cannot import htcondor. Have the condor' +
                   ' python bindings been installed?')


def ui_condor_userprio():
    """call  /bin/condor_userprio
    """
    all_users, cmd_err = subprocessSupport.iexe_cmd(
        'condor_userprio -allusers')
    if cmd_err:
        logger.log(cmd_err)
        logger.log(cmd_err, severity=logging.ERROR, logfile='error')
    return all_users


def ui_condor_status_totalrunningjobs(acctgroup=None, check_downtime=True):
    """condor_status -schedd
        -constraint '(InDownTime =!= True)&&(InDownTime =!= "True")'
        -af name TotalRunningJobs
    """

    cmd = """condor_status -schedd"""

    constraint = ""
    if acctgroup:
        if constraint:
            constraint += "&&"
        constraint += vo_constraint(acctgroup)
    if check_downtime:
        if constraint:
            constraint += "&&"
        constraint += downtime_constraint()
    if constraint:
        cmd = """%s -constraint '%s'""" % (cmd, constraint)
    cmd += """ -af name %s""" % schedd_load_metric()
    logger.log(cmd)
    all_jobs, cmd_err = subprocessSupport.iexe_cmd(cmd)
    if cmd_err:
        logger.log(cmd_err)
        logger.log(cmd_err, severity=logging.ERROR, logfile='error')

    return all_jobs


def ui_condor_queued_jobs_summary():
    """ return a summary of all running and
        queued jobs on the server
    """
    try:
        all_queued1, cmd_err = subprocessSupport.iexe_cmd(
            'condor_status -submitter -wide')
        if cmd_err:
            logger.log(cmd_err)
            logger.log(cmd_err, severity=logging.ERROR, logfile='error')

        tmp = all_queued1.split('\n')
        idx = [i for i, item in enumerate(tmp)
               if re.search('^.\s+RunningJobs', item)]
        if tmp and idx and len(idx):
            del tmp[idx[0]:]
        all_queued1 = '\n'.join(tmp)
        all_queued2, cmd_err = subprocessSupport.iexe_cmd(
            '/opt/jobsub/server/webapp/ifront_q.sh')
        if cmd_err:
            logger.log(cmd_err)
            logger.log(cmd_err, severity=logging.ERROR, logfile='error')
        all_queued = "%s\n%s" % (all_queued1, all_queued2)
        return all_queued
    except Exception:
        tbk = traceback.format_exc()
        logger.log(tbk)
        logger.log(tbk, severity=logging.ERROR, logfile='condor_commands')
        logger.log(tbk, severity=logging.ERROR, logfile='error')


def condor_header(input_switch=None):
    """generate header line for condor_q depending on input_switch
    """
    # logger.log('input_switch="%s"'%input_switch)
    if input_switch in ['long', 'better-analyze']:
        hdr = ''
    elif input_switch == 'dags':
        hdr = "JOBSUBJOBID                           OWNER    DAG_INFO          SUBMITTED     RUN_TIME   ST PRI SIZE CMD\n"
    elif input_switch == 'hold':
        hdr = "JOBSUBJOBID                           OWNER           HELD_SINCE    HOLDREASON\n"
    else:
        hdr = "JOBSUBJOBID                           OWNER           SUBMITTED     RUN_TIME   ST PRI SIZE CMD\n"
    return hdr


def condor_format(input_switch=None):
    """return format strings for condor_q depending on input_switch
    """
    # logger.log('input_switch="%s"'%input_switch)

    jobStatusStr = """'ifThenElse(JobStatus==0,"U",ifThenElse(JobStatus==1,"I",ifThenElse(TransferringInput=?=True,"<",ifThenElse(TransferringOutput=?=True,">",ifThenElse(JobStatus==2,"R",ifThenElse(JobStatus==3,"X",ifThenElse(JobStatus==4,"C",ifThenElse(JobStatus==5,"H",ifThenElse(JobStatus==6,"E",string(JobStatus))))))))))'"""

    dagStatusStr = """'ifthenelse(dagmanjobid =?= UNDEFINED, owner, dagnodename)'"""
    dagProgressStr = """'ifthenelse(DAG_NodesDone =!= UNDEFINED, strcat(string(" "),string(DAG_NodesDone),string("/"),string(DAG_NodesTotal),string(" done")),"")'"""

    runTimeStr = """ifthenelse(JobCurrentStartDate=?=UNDEFINED,0,ifthenelse(JobStatus==2,ServerTime-JobCurrentStartDate,EnteredCurrentStatus-JobCurrentStartDate))"""

    if input_switch == "long":
        fmtList = [" -l "]
    elif input_switch == "better-analyze":
        fmtList = [" -better-analyze "]
    elif input_switch == "dags":
        # don't try this at home folks
        fmtList = [
            """ -dag """,
            r""" -format '%-37s'  'regexps("((.+)\#(.+)\#(.+))",globaljobid,"\\3@\\2 ")'""",
            """ -format ' %-1s '""", """string(" ")""",
            """ -format ' %-16s '""", dagStatusStr,
            """ -format ' %-11s ' 'formatTime(QDate,"%m/%d %H:%M")'""",
            """ -format '%3d+' """, """'int(""", runTimeStr, """/(3600*24))'""",
            """ -format '%02d' """, """'int(""", runTimeStr, """/3600)-int(24*INT(""", runTimeStr, """/(3600*24)))'""",
            """ -format ':%02d' """, """'int(""", runTimeStr, """/60)-int(60*INT(INT(""", runTimeStr, """/60)/60))'""",
            """ -format ':%02d' """, """'""", runTimeStr, """-int(60*int(""", runTimeStr, """/60))'""",
            """ -format ' %-2s' """, jobStatusStr,
            """ -format '%3d ' JobPrio """,
            """ -format ' %4.1f ' ImageSize/1024.0 """,
            r""" -format '%-30s' 'regexps(".*\/(.+)",cmd,"\\1")'""",
            """ -format '%-10s' """, dagProgressStr,
            """ -format '\\n' Owner """,
        ]
    elif input_switch == "hold":
        fmtList = [
            r""" -format '%-37s'  'regexps("((.+)\#(.+)\#(.+))",globaljobid,"\\3@\\2 ")'""",
            """ -format ' %-14s ' Owner """,
            """ -format ' %-11s ' 'formatTime(EnteredCurrentStatus,"%m/%d %H:%M")'""",
            """ -format '  %s' HoldReason""",
            """ -format '\\n' Owner """,
        ]
    else:
        fmtList = [
            r""" -format '%-37s' 'regexps("((.+)\#(.+)\#(.+))",globaljobid,"\\3@\\2 ")'""",
            """ -format ' %-14s ' Owner """,
            """ -format ' %-11s ' 'formatTime(QDate,"%m/%d %H:%M")'""",
            """ -format '%3d+' """, """'int(""", runTimeStr, """/(3600*24))'""",
            """ -format '%02d' """, """'int(""", runTimeStr, """/3600)-int(24*INT(""", runTimeStr, """/(3600*24)))'""",
            """ -format ':%02d' """, """'int(""", runTimeStr, """/60)-int(60*INT(INT(""", runTimeStr, """/60)/60))'""",
            """ -format ':%02d' """, """'""", runTimeStr, """-int(60*int(""", runTimeStr, """/60))'""",
            """ -format ' %-2s' """, jobStatusStr,
            """ -format '%3d ' JobPrio """,
            """ -format ' %4.1f ' ImageSize/1024.0 """,
            r""" -format '%-30s ' 'regexps(".*\/(.+)",cmd,"\\1")'""",
            """ -format '\\n' Owner """,
        ]

    return ' '.join(fmtList)


def constructFilter(acctgroup=None, uid=None, jobid=None, jobstatus=None):
    """generate a constraint for condor_q
    """
    if acctgroup == 'None':
        acctgroup = None
    if uid == 'None':
        uid = None
    if jobid == 'None':
        jobid = None
    if jobstatus == 'None':
        jobstatus = None
    lorw = ' '
    if acctgroup is None:
        ac_cnst = 'True'
    else:
        ac_cnst = """regexp("group_%s.*",AccountingGroup)""" % acctgroup

    if uid is None:
        usr_cnst = 'True'
    else:
        usr_cnst = 'Owner=="%s"' % uid

    if jobid is None:
        job_cnst = 'True'
    elif jobid.find('@') >= 0:
        spx = jobid.split('@')
        clusterid = spx[0]
        host = '@'.join(spx[1:])
        cluster_pts = clusterid.split('.')
        while '' in cluster_pts:
            cluster_pts.remove('')
        cluster_pts.append('.*')
        job_cnst = r"""regexp("%s#%s\.%s#.*",GlobalJobId)""" % (host,
                                                                cluster_pts[0],
                                                                cluster_pts[1]
                                                                )
    else:
        lorw = ' '
        job_cnst = 'ClusterID==%d' % (math.trunc(float(jobid)))
    if jobstatus is None:
        jstat_cnst = 'True'
    else:
        jstat_cnst = 'JobStatus==%s' % (
            JOBSTATUS_DICT.get(jobstatus.lower(), 5))
    my_filter = " %s -constraint '%s && %s && %s && %s' " % (
        lorw, ac_cnst, usr_cnst, job_cnst, jstat_cnst)
    return my_filter


def ui_condor_q(a_filter=None, a_format=None, a_key=None):
    """
    condor_q
        args:
            a_filter: a condor constraint, usually built by constuct_filter
            a_format: one of 'long', 'dags', 'better-analyze'
            a_key: Key list whose values should be printed from each job.
                   This list will follow -af in the condor_q command.
                   Cannot be used with a_format currently
    """
    #logger.log('filter=%s format=%s'%(filter,format))
    # Until we figure out the various possible modes, can't use a_format and
    # a_key at the same time
    try:
        assert None in (a_format, a_key)
    except AssertionError:
        tb = traceback.format_exc()
        logger.log(tb, severity=logging.ERROR)
        logger.log(tb, severity=logging.ERROR, logfile='error')
        # Do we want an exit here?
        return tb

    if a_key is None:
        hdr = condor_header(a_format)
        fmt = condor_format(a_format)
    else:
        hdr = fmt = ''
    s_list = schedd_list()
    all_jobs = hdr
    cqef = condor_q_extra_flags()
    for schedd in s_list:
        try:
            if a_filter is None:
                cmd = 'condor_q %s -name %s  %s ' % (cqef, schedd, fmt)
            else:
                cmd = 'condor_q %s -name %s %s %s' % (
                    cqef, schedd, fmt, a_filter)
            if a_key is not None:
                cmd = cmd + ' -af %s' % ' '.join((str(elt) for elt in a_key))
            jobs, cmd_err = subprocessSupport.iexe_cmd(cmd)
            if cmd_err:
                logger.log(cmd_err)
                logger.log(cmd_err, severity=logging.ERROR, logfile='error')
            user = 'Unknown'
            try:
                c_dn = get_client_dn()
                pts = c_dn.split(':')
                user = pts[-1]
            except Exception:
                pass
            log_cmd = "[user:%s] %s" % (
                user, cmd)
            logger.log(log_cmd, logfile='condor_commands')
            all_jobs += jobs
            # logger.log("cmd=%s"%cmd)
            # logger.log("rslt=%s"%all_jobs)
            # return hdr + all_jobs
        except Exception:
            tb = traceback.format_exc()
            logger.log(tb, severity=logging.ERROR)
            logger.log(tb, severity=logging.ERROR, logfile='error')
            no_jobs = "All queues are empty"
            if len(re.findall(no_jobs, tb)):
                # return no_jobs
                empty = schedd + ": " + no_jobs + "\n"
                all_jobs += empty
            else:
                cherrypy.response.status = 500
                if 'CEDAR' in tb or 'SECMAN' in tb:
                    err = 'HTCondor schedd %s appears to be too busy ' % schedd
                    err += 'to respond. Please try again in a few minutes. '
                    err += tb[-1]
                    logger.log(err, severity=logging.ERROR,
                               logfile='condor_commands')
                    logger.log(err, severity=logging.ERROR, logfile='error')
                    return err
                else:
                    logger.log(tb, severity=logging.ERROR,
                               logfile='condor_commands')
                    logger.log(tb, severity=logging.ERROR, logfile='error')
                    return tb
    return all_jobs


def condor_userprio():
    """
    list users condor priorities
    """
    cmd = 'condor_userprio -allusers'
    users = ''
    try:
        users, cmd_err = subprocessSupport.iexe_cmd(cmd)
        if cmd_err:
            logger.log(cmd_err)
            logger.log(cmd_err, severity=logging.ERROR, logfile='error')
        # logger.log("cmd=%s"%cmd)
        # logger.log("rslt=%s"%all_jobs)
        return users
    except Exception:
        tbk = traceback.format_exc()
        logger.log(tbk, severity=logging.ERROR)
        return tbk


def iwd_condor_q(a_filter, a_part='iwd'):
    """
    return the iwd of a job or multiple jobs
    """
    cmd = 'condor_q -af %s  %s' % (a_part, a_filter)
    iwd = ''
    try:
        iwd, cmd_err = subprocessSupport.iexe_cmd(cmd)
        if cmd_err:
            logger.log(cmd_err)
            logger.log(cmd_err, severity=logging.ERROR, logfile='error')
        # logger.log("cmd=%s"%cmd)
        # logger.log("rslt=%s"%all_jobs)
        return iwd
    except Exception:
        tbk = traceback.format_exc()
        logger.log(tbk, severity=logging.ERROR)
        no_jobs = "All queues are empty"
        if len(re.findall(no_jobs, tbk)):
            return no_jobs
        else:
            cherrypy.response.status = 500
            if 'ailed to connect' in tbk:
                err = 'Failed to connect to condor schedd '
                logger.log(err, severity=logging.ERROR,
                           logfile='condor_commands')
                logger.log(err, severity=logging.ERROR, logfile='error')
                return err
            else:
                logger.log(tbk, severity=logging.ERROR,
                           logfile='condor_commands')
                logger.log(tbk, severity=logging.ERROR, logfile='error')
                return tbk


def api_condor_q(acctgroup, uid, convert=False):
    """ Uses the Condor Python bindings to get information for scheduled jobs.
        Returns a map of objects with the Cluster Id as the key
    """

    schedd = condor.Schedd()
    results = schedd.query('Owner =?= "%s"' % uid)
    all_jobs = dict()
    for classad in results:
        env = dict([x.split('=') for x in classad['Env'].split(';')])
        if env.get('EXPERIMENT') == acctgroup:
            key = classad['ClusterId']
            if convert is True:
                classad = classad_to_dict(classad)
            all_jobs[key] = classad
    return all_jobs


def classad_to_dict(classad):
    """ Converts a ClassAd object to a dictionary.
    Used for serialization to JSON.
    """
    job_dict = dict()
    for k, v in classad.items():
        job_dict[repr(k)] = repr(v)
    return job_dict


def collector_host():
    """
    return the condor collector host name
    """
    try:
        hosts, cmd_err = subprocessSupport.iexe_cmd(
            """condor_status -collector -af Machine""")
        if cmd_err:
            logger.log(cmd_err)
            logger.log(cmd_err, severity=logging.ERROR, logfile='error')
        host_list = hosts.split('\n')
        while '' in host_list:
            host_list.remove('')
        host = host_list[randint(0, len(host_list) - 1)]
        logger.log('choosing %s from %s' % (host, host_list))
        return host
    except Exception:
        tbk = traceback.format_exc()
        logger.log(tbk)
        logger.log(tbk, severity=logging.ERROR, logfile='condor_commands')
        logger.log(tbk, severity=logging.ERROR, logfile='error')


def schedd_list(acctgroup=None, check_downtime=True):
    """
    return a list of all the schedds
    """

    try:
        cmd = """condor_status -schedd -af name """
        constraint = ""
        if acctgroup:
            if constraint:
                constraint += "&&"
            constraint += vo_constraint(acctgroup)
        if check_downtime:
            if constraint:
                constraint += "&&"
            constraint += downtime_constraint()
        if constraint:
            cmd = """%s -constraint '%s'""" % (cmd, constraint)
        logger.log(cmd)
        schedds, cmd_err = subprocessSupport.iexe_cmd(cmd)
        if cmd_err:
            logger.log(cmd_err)
            logger.log(cmd_err, severity=logging.ERROR, logfile='error')
        return schedds.split()
    except Exception:
        tbk = traceback.format_exc()
        logger.log(tbk, severity=logging.ERROR)
        logger.log(tbk, severity=logging.ERROR, logfile='condor_commands')
        logger.log(tbk, severity=logging.ERROR, logfile='error')


def condor_q_extra_flags():
    jcp = JobsubConfigParser.JobsubConfigParser()
    cqef = jcp.get('default', 'condor_q_extra_flags')
    if not cqef:
        cqef = ''
    return cqef


def downtime_constraint():
    jcp = JobsubConfigParser.JobsubConfigParser()
    dt_constraint = jcp.get('default', 'downtime_constraint')
    if not dt_constraint:
        dt_constraint = "InDownTime=!=True"
    return dt_constraint


def vo_constraint(acctgroup):
    if not acctgroup:
        return "True"
    jcp = JobsubConfigParser.JobsubConfigParser()
    voc = jcp.get(acctgroup, 'vo_constraint')
    if not voc:
        voc = """(SupportedVOList=?=undefined||stringlistmember("{0}",SupportedVOList))"""
    if "{0}" in voc:
        return voc.format(acctgroup)
    else:
        return voc


def schedd_load_metric():
    jcp = JobsubConfigParser.JobsubConfigParser()
    metric = jcp.get('default', 'schedd_load_metric')
    if not metric:
        metric = "TotalRunningJobs"
    return metric


def best_schedd(acctgroup=None, check_remote_schedds=False):
    """
    return schedd with lowest load metric subject to constraints
    """

    try:
        cmd = """condor_status -schedd -af name %s """ % schedd_load_metric()
        constraint = """%s&&%s""" % (vo_constraint(acctgroup),
                                     downtime_constraint())
        if not check_remote_schedds:
            _name = "%s" % socket.gethostname()
            constraint += """&&regexp(".*%s.*",Name)""" % _name

        cmd += """ -constraint '%s'""" % constraint

        logger.log(cmd)
        cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd)
        if cmd_err:
            logger.log(cmd_err)
            logger.log(cmd_err, severity=logging.ERROR, logfile='error')
        cycle = 1e+99
        schedd = "no_schedds_meet_submission_criteria"
        logger.log('cmd: %s cmd_out:%s' % (cmd, cmd_out))
        for line in cmd_out.split('\n'):
            vals = line.split(' ')
            logger.log(vals)
            if len(vals) == 2:
                nm = vals[0]
                val = float(vals[-1])
                if val < 0:
                    val *= -1.0
                if val <= cycle:
                    schedd = nm
                    cycle = val
        logger.log('chose %s as best schedd' % schedd)
        return schedd
    except Exception:
        tbk = traceback.format_exc()
        #logger.log(cmd_err, severity=logging.ERROR)
        logger.log(tbk, severity=logging.ERROR)
        logger.log(tbk, severity=logging.ERROR, logfile='condor_commands')
        logger.log(tbk, severity=logging.ERROR, logfile='error')


def schedd_recent_duty_cycle(schedd_nm=None):
    """
    return condor_status -schedd -af RecentDaemonCoreDutyCycle
        -constraint 'Name=?="schedd_name"'
    """

    try:
        if schedd_nm is None:
            schedd_nm = schedd_name()
        cmd = """condor_status -schedd -af RecentDaemonCoreDutyCycle """
        cmd += """-constraint 'Name=?="%s"'""" % schedd_nm
        cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd)
        if cmd_err:
            logger.log(cmd_err)
            logger.log(cmd_err, severity=logging.ERROR, logfile='error')
        duty_cycle = float(cmd_out)

        return duty_cycle
    except Exception:
        tbk = traceback.format_exc()
        logger.log(cmd_err, severity=logging.ERROR)
        logger.log(tbk, severity=logging.ERROR)
        logger.log(tbk, severity=logging.ERROR, logfile='condor_commands')
        logger.log(tbk, severity=logging.ERROR, logfile='error')


def schedd_name(arglist=None):
    """
    return name of the local schedd
    will not work properly with multiple schedds on a host
    """

    # logger.log(arglist)
    _list = schedd_list()
    if len(_list) == 1:
        return _list[0]
    _name = "%s" % socket.gethostname()
    if arglist and len(arglist) > 0:
        i = 0
        for arg in arglist:
            arg = str(arg)
            #logger.log("arg %s i %s"%(arg,i))
            if arg == '--schedd':
                _schedd = str(arglist[i + 1])
                if _schedd in _list:
                    return _schedd

            if arg.find('--schedd=') == 0:
                argparts = arg.split('=')
                _schedd = '='.join(argparts[1:])
                if _schedd in _list:
                    return _schedd
            i = i + 1
    return _name


if __name__ == '__main__':
    # export PYTHONPATH=jobsub/server/webapp
    # export PYTHONPATH=$PYTHONPATH:jobsub/lib/logger
    # export PYTHONPATH=$PYTHONPATH:jobsub/lib/JobsubConfigParser
    # export JOBSUB_INI_FILE=/opt/jobsub/server/conf.jobsub.ini
    # export JOBSUB_USE_FAKE_LOGGER=true
    # possibly export JOBSUB_SUPPRESS_LOG_OUTPUT=true
    print 'put some test code here'
