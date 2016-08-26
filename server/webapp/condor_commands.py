import cherrypy
import logger
import logging
import traceback
import math
import platform
import subprocessSupport
import socket
import re
import auth
from random import randint


jobstatus_dict = {'unexpanded': 0, 'idle': 1, 'run': 2, 'running': 2,
                  'removed': 3, 'completed': 4, 'held': 5, 'hold': 5, 'error': 6}
if platform.system() == 'Linux':
    try:
        import htcondor as condor
    except:
        logger.log('Cannot import htcondor. Have the condor' +
                   ' python bindings been installed?')


def ui_condor_userprio():
    all_users, cmd_err = subprocessSupport.iexe_cmd(
        'condor_userprio -allusers')
    return all_users


def ui_condor_status_totalrunningjobs():
    all_jobs, cmd_err = subprocessSupport.iexe_cmd(
        """condor_status -schedd   -constraint '(Indowntime =!= True)&&(InDowntime =!= "True")' -af name totalrunningjobs""")
    return all_jobs


def ui_condor_queued_jobs_summary():
    try:
        all_queued1, cmd_err = subprocessSupport.iexe_cmd(
            'condor_status -submitter -wide')
        tmp = all_queued1.split('\n')
        idx = [i for i, item in enumerate(tmp)
               if re.search('^.\s+RunningJobs', item)]
        if tmp and idx and len(idx):
            del tmp[idx[0]:]
        all_queued1 = '\n'.join(tmp)
        all_queued2, cmd_err = subprocessSupport.iexe_cmd(
            '/opt/jobsub/server/webapp/ifront_q.sh')
        all_queued = "%s\n%s" % (all_queued1, all_queued2)
        return all_queued
    except:
        tb = traceback.format_exc()
        logger.log(tb)
        logger.log(tb, severity=logging.ERROR, logfile='condor_commands')
        logger.log(tb, severity=logging.ERROR, logfile='error')


def condor_header(inputSwitch=None):
    # logger.log('inputSwitch="%s"'%inputSwitch)
    if inputSwitch in ['long', 'better-analyze']:
        hdr = ''
    elif inputSwitch == 'dags':
        hdr = "JOBSUBJOBID                           OWNER    DAG_INFO          SUBMITTED     RUN_TIME   ST PRI SIZE CMD\n"
    elif inputSwitch == 'hold':
        hdr = "JOBSUBJOBID                           OWNER           HELD_SINCE    HOLDREASON\n"
    else:
        hdr = "JOBSUBJOBID                           OWNER           SUBMITTED     RUN_TIME   ST PRI SIZE CMD\n"
    return hdr


def condor_format(inputSwitch=None):
    # logger.log('inputSwitch="%s"'%inputSwitch)

    jobStatusStr = """'ifThenElse(JobStatus==0,"U",ifThenElse(JobStatus==1,"I",ifThenElse(TransferringInput=?=True,"<",ifThenElse(TransferringOutput=?=True,">",ifThenElse(JobStatus==2,"R",ifThenElse(JobStatus==3,"X",ifThenElse(JobStatus==4,"C",ifThenElse(JobStatus==5,"H",ifThenElse(JobStatus==6,"E",string(JobStatus))))))))))'"""

    dagStatusStr = """'ifthenelse(dagmanjobid =!= UNDEFINED, strcat(string("Section_"),string(jobsubjobsection)),ifthenelse(DAG_NodesDone =!= UNDEFINED, strcat(string("dag, "),string(DAG_NodesDone),string("/"),string(DAG_NodesTotal),string(" done")),"") )'"""

    runTimeStr = """ifthenelse(JobStartDate=?=UNDEFINED,0,ifthenelse(CompletionDate==0,ServerTime-JobStartDate,CompletionDate-JobStartDate))"""

    if inputSwitch == "long":
        fmtList = [" -l "]
    elif inputSwitch == "better-analyze":
        fmtList = [" -better-analyze "]
    elif inputSwitch == "dags":
        # don't try this at home folks
        fmtList = [
            """ -dag """,
            """ -format '%-37s'  'regexps("((.+)\#(.+)\#(.+))",globaljobid,"\\3@\\2 ")'""",
            """ -format ' %-8s' 'ifthenelse(dagmanjobid =?= UNDEFINED, string(owner),strcat("  "))'""",
            """ -format ' %-16s '""", dagStatusStr,
            """ -format ' %-11s ' 'formatTime(QDate,"%m/%d %H:%M")'""",
            """ -format '%3d+' """, """'int(""", runTimeStr, """/(3600*24))'""",
            """ -format '%02d' """, """'int(""", runTimeStr, """/3600)-int(24*INT(""", runTimeStr, """/(3600*24)))'""",
            """ -format ':%02d' """, """'int(""", runTimeStr, """/60)-int(60*INT(INT(""", runTimeStr, """/60)/60))'""",
            """ -format ':%02d' """, """'""", runTimeStr, """-int(60*int(""", runTimeStr, """/60))'""",
            """ -format ' %-2s' """, jobStatusStr,
            """ -format '%3d ' JobPrio """,
            """ -format ' %4.1f ' ImageSize/1024.0 """,
            """ -format '%-30s' 'regexps(".*\/(.+)",cmd,"\\1")'""",
            """ -format '\\n' Owner """,
        ]
    elif inputSwitch == "hold":
        fmtList = [
            """ -format '%-37s'  'regexps("((.+)\#(.+)\#(.+))",globaljobid,"\\3@\\2 ")'""",
            """ -format ' %-14s ' Owner """,
            """ -format ' %-11s ' 'formatTime(EnteredCurrentStatus,"%m/%d %H:%M")'""",
            """ -format '  %s' HoldReason""",
            """ -format '\\n' Owner """,
        ]
    else:
        fmtList = [
            """ -format '%-37s' 'regexps("((.+)\#(.+)\#(.+))",globaljobid,"\\3@\\2 ")'""",
            """ -format ' %-14s ' Owner """,
            """ -format ' %-11s ' 'formatTime(QDate,"%m/%d %H:%M")'""",
            """ -format '%3d+' """, """'int(""", runTimeStr, """/(3600*24))'""",
            """ -format '%02d' """, """'int(""", runTimeStr, """/3600)-int(24*INT(""", runTimeStr, """/(3600*24)))'""",
            """ -format ':%02d' """, """'int(""", runTimeStr, """/60)-int(60*INT(INT(""", runTimeStr, """/60)/60))'""",
            """ -format ':%02d' """, """'""", runTimeStr, """-int(60*int(""", runTimeStr, """/60))'""",
            """ -format ' %-2s' """, jobStatusStr,
            """ -format '%3d ' JobPrio """,
            """ -format ' %4.1f ' ImageSize/1024.0 """,
            """ -format '%-30s ' 'regexps(".*\/(.+)",cmd,"\\1")'""",
            """ -format '\\n' Owner """,
        ]

    return ' '.join(fmtList)


def munge_jobid(theInput=None):
    header = ['ID', ' ', ' ', ' ', 'OWNER', 'SUBMITTED',
              'RUN_TIME', 'ST', 'PRI', 'SIZE', 'CMD']
    if theInput == None:
        return None
    linput = theInput.split('\n')
    loutput = []
    loutput.append("\t".join(header))
    for line in linput:
        if line == '':
            continue
        llout = line.split()
        loutput.append("\t".join(llout))
    return "\n".join(loutput)


def constructFilter(acctgroup=None, uid=None, jobid=None, jobstatus=None):
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
        x = jobid.split('@')
        clusterid = x[0]
        host = '@'.join(x[1:])
        if clusterid.find('.') < 0:
            clusterid = clusterid + '.0'
        job_cnst = """regexp("%s#%s.*",GlobalJobId)""" % (host, clusterid)
    else:
        lorw = ' '
        job_cnst = 'ClusterID==%d' % (math.trunc(float(jobid)))
    if jobstatus is None:
        jstat_cnst = 'True'
    else:
        jstat_cnst = 'JobStatus==%s' % (
            jobstatus_dict.get(jobstatus.lower(), 5))
    my_filter = " %s -constraint '%s && %s && %s && %s' " % (
        lorw, ac_cnst, usr_cnst, job_cnst, jstat_cnst)
    return my_filter


def contains_jobid(a_filter=""):
    if "GLOBALJOBID" in a_filter.upper() or "CLUSTERID" in a_filter.upper():
        return True
    return False


def ui_condor_history(a_filter=None, a_format=None):
    hdr = condor_header(a_format)
    if a_filter is None:
        cmd = 'condor_history %s' % condor_format(a_format)
    else:
        if contains_jobid(a_filter):
            a_filter = "%s %s" % (a_filter, "-match 1")
        cmd = 'condor_history %s %s' % (condor_format(a_format), a_filter)
    try:
        all_jobs, cmd_err = subprocessSupport.iexe_cmd(cmd)
        return hdr + all_jobs
    except:
        cherrypy.response.status = 500
        tb = traceback.format_exc()
        logger.log(tb, severity=logging.ERROR)
        logger.log(tb, severity=logging.ERROR, logfile='condor_commands')
        logger.log(tb, severity=logging.ERROR, logfile='error')
        return tb


def ui_condor_q(a_filter=None, a_format=None):
    #logger.log('filter=%s format=%s'%(filter,format))
    hdr = condor_header(a_format)
    fmt = condor_format(a_format)
    s_list = schedd_list()
    all_jobs = hdr
    for schedd in s_list:
        try:
            if a_filter is None:
                cmd = 'condor_q -name %s  %s ' % (schedd, fmt)
            else:
                cmd = 'condor_q -name %s %s %s' % (schedd, fmt, a_filter)
            jobs, cmd_err = subprocessSupport.iexe_cmd(cmd)
            dn = auth.get_client_dn()
            pts = dn.split(':')
            user = pts[-1]
            log_cmd = "[user:%s] condor_q -name %s %s" % (
                user, schedd, a_filter)

            logger.log(log_cmd, logfile='condor_commands')
            all_jobs += jobs
            # logger.log("cmd=%s"%cmd)
            # logger.log("rslt=%s"%all_jobs)
            # return hdr + all_jobs
        except:
            tb = traceback.format_exc()
            logger.log(tb, severity=logging.ERROR)
            no_jobs = "All queues are empty"
            if len(re.findall(no_jobs, tb)):
                # return no_jobs
                empty = schedd + ": " + no_jobs + "\n"
                all_jobs += empty
            else:
                cherrypy.response.status = 500
                if 'ailed to connect' in tb:
                    err = 'Failed to connect to condor schedd %s' % schedd
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


def iwd_condor_q(a_filter, a_part='iwd'):
    cmd = 'condor_q -af %s  %s' % (a_part, a_filter)
    iwd = ''
    try:
        iwd, cmd_err = subprocessSupport.iexe_cmd(cmd)
        # logger.log("cmd=%s"%cmd)
        # logger.log("rslt=%s"%all_jobs)
        return iwd
    except:
        tb = traceback.format_exc()
        logger.log(tb, severity=logging.ERROR)
        no_jobs = "All queues are empty"
        if len(re.findall(no_jobs, tb)):
            return no_jobs
        else:
            cherrypy.response.status = 500
            if 'ailed to connect' in tb:
                err = 'Failed to connect to condor schedd %s' % schedd
                logger.log(err, severity=logging.ERROR,
                           logfile='condor_commands')
                logger.log(err, severity=logging.ERROR, logfile='error')
                return err
            else:
                logger.log(tb, severity=logging.ERROR,
                           logfile='condor_commands')
                logger.log(tb, severity=logging.ERROR, logfile='error')
                return tb


def all_known_jobs(acct_group, uid=None, jobid=None):
    my_filter = constructFilter(acct_group, uid, jobid)
    queued = ui_condor_q(my_filter)
    if len(queued.split('\n')) < 1:
        queued = ''
    history = ui_condor_history(my_filter)
    if len(history.split('\n')) < 1:
        history = ''
    all = queued + history
    return all


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
    try:
        hosts, cmd_err = subprocessSupport.iexe_cmd(
            """condor_config_val collector_host """)
        host_x = hosts.split('\n')
        host_list = host_x[0].split(',')
        host = host_list[randint(0, len(host_list) - 1)]
        logger.log('choosing %s from %s' % (host, host_list))
        return host
    except:
        tb = traceback.format_exc()
        logger.log(tb)
        logger.log(tb, severity=logging.ERROR, logfile='condor_commands')
        logger.log(tb, severity=logging.ERROR, logfile='error')


def schedd_list():
    try:
        schedds, cmd_err = subprocessSupport.iexe_cmd(
            """condor_status -schedd -af name """)
        return schedds.split()
    except:
        tb = traceback.format_exc()
        logger.log(tb, severity=logging.ERROR)
        logger.log(tb, severity=logging.ERROR, logfile='condor_commands')
        logger.log(tb, severity=logging.ERROR, logfile='error')


def schedd_name(arglist=None):
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
