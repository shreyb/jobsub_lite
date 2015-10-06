import cherrypy
import logger
import traceback
import os
import sys
import subprocessSupport
import sqlite3
import re
import socket
import JobsubConfigParser


def fmtStr():
    return "%-38s  %-19s  %-19s %-19s %-3s      %s"

def sql_header(inputSwitch=None):
    hdr = fmtStr() % ("JOBSUBJOBID", "OWNER", "SUBMITTED","FINISHED","ST","CMD")
    return hdr


def constructQuery( acctgroup=None, uid=None, jobid=None):
    if acctgroup=='None':
        acctgroup=None
    if uid=='None':
        uid=None
    if jobid=='None':
        jobid=None
    cnt = 0
    flt = "select * from jobsub_history  "
    if acctgroup is not  None:
        flt += 'where acctgroup="%s" ' % acctgroup
        cnt += 1
    if uid is not None:
        if cnt > 0:
            flt += " and "
        else:
            flt += " where "
        flt += ' Owner="%s" '%uid
        cnt += 1
    if jobid is not None:
        if cnt > 0:
            flt += " and "
        else:
            flt += " where "
        flt += ' jobsubjobid = "%s" ' % jobid
    flt += ";"
    return flt





def iwd_jobsub_history(query):
    hdr = sql_header()
    hostname = socket.gethostname()
    p = JobsubConfigParser.JobsubConfigParser()
    history_db = p.get(hostname,'history_db') 
    if not history_db:
        history_db = "/fife/local/scratch/history/%s/jobsub_history.db" % hostname
    conn = sqlite3.connect(history_db)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    rslt=[hdr]
    rslt=None
    for row in c.execute(query):
        rslt = row['iwd']
    return rslt

def jobsub_history(query):
    hdr = sql_header()
    hostname = socket.gethostname()
    p = JobsubConfigParser.JobsubConfigParser()
    history_db = p.get(hostname,'history_db') 
    if not history_db:
        history_db = "/fife/local/scratch/history/%s/jobsub_history.db" % hostname
    conn = sqlite3.connect(history_db)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    rslt=[hdr]
    for row in c.execute(query):
        cmd = re.sub('_20[1-3][0-9][0-1][0-9].*',' ',row['ownerjob'])
        if row['jobstatus']=='X':
            cdate = ' '
        else:
            cdate = row['completiondate']
        r_row = fmtStr() %\
                (row['jobsubjobid'],row['owner'],row['qdate'],
                        cdate ,row['jobstatus'],
                        cmd)
        rslt.append(r_row)
    return rslt
