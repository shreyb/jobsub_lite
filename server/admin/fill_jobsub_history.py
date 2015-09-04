#!/bin/env python
import sys
import os
import string
import subprocessSupport
import logger
import logging
import sqlite3
import socket
import shutil
import JobsubConfigParser

def createSchemaSQL():
    cmd = """
    create table if not exists load_history(
    history_file text PRIMARY KEY,
    jobsub server text,
    loaded datetime
    );
    create table if not exists jobsub_history( 
    jobsubjobid text PRIMARY KEY ,
    acctgroup text,  
    owner text, 
    ownerjob text, 
    iwd text, 
    qdate datetime, 
    jobcurrentstartdate datetime, 
    completiondate datetime, 
    jobstatus datetime, 
    numjobstarts integer
    );
    """
    return cmd


def createHistoryDump(historyFileName='history'):
    cmd = """condor_history -file %s -af globaljobid iwd  
             jobstatus qdate jobcurrentstartdate 
             completiondate numjobstarts cmd""" % historyFileName
    hist, cmd_err = subprocessSupport.iexe_cmd(cmd)
    int_fname = "%s.dat" % historyFileName
    with open(int_fname,'w') as f:
        for line in hist.split('\n'):
            f.write("%s\n" % line)
    f.close()




def createSqlFile(historyFileName, serverName=None):
    f_outname = "%s.sql" % historyFileName
    f_inname = "%s.dat" % historyFileName
    f_out = open(f_outname ,'w')
    if historyFileName != 'partial.history':
        load_hist = """insert into load_history values """
        load_hist += """('%s','%s',datetime('now'));""" %\
                        (historyFileName, serverName)
        f_out.write('%s\n' % load_hist)
    with open(f_inname, 'r') as f_in:
        for line in f_in:
            line = line.replace('undefined','0')
            wrds = string.split(line)
            if len(wrds) > 0:
                if '#' in wrds[0]:
                    idparts = string.split(wrds[0], '#')
                    jobsubjobid = "%s@%s"%(idparts[1], idparts[0])
                    ownerjob = os.path.basename(wrds[7])
                    iwd = wrds[1]
                    iwdparts = string.split(iwd, '/')
                    acctgroup = iwdparts[-3]
                    owner = iwdparts[-2]
                    jobstatus = 'C'
                    if wrds[2] == '3':
                        jobstatus = 'X'
                    qdate = wrds[3]
                    jobcurrentstartdate = wrds[4]
                    completiondate = wrds[5]
                    numjobstarts = wrds[6]
                    tmpl= """insert into jobsub_history values("""
                    tmpl += """'%s','%s','%s','%s','%s',"""
                    tmpl += """datetime(%s,'unixepoch', 'localtime'),"""
                    tmpl += """datetime(%s,'unixepoch', 'localtime'),"""
                    tmpl += """datetime(%s,'unixepoch', 'localtime'),'%s',%s);\n"""
                    insertStr = tmpl% (jobsubjobid,acctgroup,owner,ownerjob,iwd,
                            qdate,
                            jobcurrentstartdate,
                            completiondate,
                            jobstatus,numjobstarts)

                    f_out.write(insertStr)
    f_out.close()

def doStuff():
    host = socket.gethostname()
    p = JobsubConfigParser.JobsubConfigParser()
    history_db = p.get(host,'history_db')
    logger.log("history_db=%s"%history_db,logfile="fill_jobsub_history")
    dir = os.path.dirname(history_db)
    logger.log("changing to %s"%dir, logfile="fill_jobsub_history")
    os.chdir(dir)
    try:
        os.makedirs('work')
    except:
        pass
    try:
        shutil.copy('jobsub_history.db', 'work')
        os.chdir('work')
        cmd = "condor_config_val HISTORY"
        histfile , cmd_err = subprocessSupport.iexe_cmd(cmd)
        cmd = "rsync %s . --size-only --backup --times" % histfile
        logger.log(cmd, logfile="fill_jobsub_history")
        cmd_out , cmd_err = subprocessSupport.iexe_cmd(cmd)
        logger.log(cmd_out, logfile="fill_jobsub_history")
        logger.log(cmd_err, logfile="fill_jobsub_history")
        num_lines = open('history').read().count('\n')
        logger.log("history file has %s lines" % num_lines, logfile="fill_jobsub_history")
        if os.path.exists('history~'):
            num_lines_old = open('history~').read().count('\n')
            tailsize = num_lines - num_lines_old
            if tailsize > 0:
                cmd = "tail --lines %s history " % tailsize
                logger.log(cmd, logfile="fill_jobsub_history")
                cmd_out , cmd_err = subprocessSupport.iexe_cmd(cmd)
                fname='partial_history'
                with open(fname,'w') as f:
                    for line in cmd_out.split('\n'):
                        f.write("%s\n" % line)
                f.close()
        else:
            fname='history'
        createHistoryDump(fname)
        createSqlFile(fname)
        loadDatabase(fname)
        shutil.copy('jobsub_history.db', history_db)

    except:
        logger.log(sys.exc_info()[1],severity=logging.ERROR, logfile="fill_jobsub_history")


def loadDatabase(filebase):
    dir = os.path.dirname(filebase)
    fb = os.path.basename(filebase)
    if dir:
        logger.log("changing to %s"%dir , logfile="fill_jobsub_history")
        os.chdir(dir) 
    conn = sqlite3.connect('jobsub_history.db')
    c = conn.cursor()
    sql_file = "%s.sql" % fb
    num_total = 0
    num_good = 0
    num_bad = 0
    with open(sql_file,'r') as f:
        for line in f:
            num_total += 1
            try:
                c.execute(line)
                conn.commit()
                num_good += 1
            except sqlite3.Error as e:
                msg = "%s " %(str(e))
                logger.log(line , severity=logging.ERROR, logfile="fill_jobsub_history")
                logger.log(msg , severity=logging.ERROR, logfile="fill_jobsub_history")
                num_bad += 1
   
    totals = "%s lines in upload  %s successfully loaded  %s failed " % (num_total, num_good, num_bad)
    logger.log(totals, logfile="fill_jobsub_history")
    conn.close()

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'load-database-from-sql':
       loadDatabase(sys.argv[2])
    else:
        doStuff()
    #createHistoryDump(sys.argv[1])
    #createSqlFile(sys.argv[1], serverName=sys.argv[2])

