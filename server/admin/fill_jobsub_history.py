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
import optparse
import time
import JobsubConfigParser


def createDB(dir=None):
    if dir:
        os.chdir(dir)
    else:
        dir = os.getcwd()
    logger.log('in directory %s'%dir, logfile="fill_jobsub_history")
    sql1 = """
        create table if not exists load_history(
        history_file text PRIMARY KEY,
        jobsub server text,
        loaded datetime
        );
    """
    sql2="""    
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
    executeSQLCmds([sql1, sql2])

def checkHistoryDB():
    conn = sqlite3.connect('jobsub_history.db')
    c = conn.cursor()
    try:
        sql = "select count(*) from jobsub_history"
        c.execute(sql)
        conn.commit()
    except sqlite3.Error as e:
        logger.log('jobsub_history.db not found, attempting to create',
                   severity=logging.ERROR,
                   logfile="fill_jobsub_history")
        logger.log('jobsub_history.db not found, attempting to create',
                   severity=logging.ERROR,
                   logfile="error")
        createDB()
    conn.close()


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
    if historyFileName == 'partial_history':
        now = time.time()
        historyFileName = "%s.%s" % (historyFileName, now)
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


def historyDBDir():
    host = socket.gethostname()
    p = JobsubConfigParser.JobsubConfigParser()
    history_db = p.get(host,'history_db')
    logger.log("history_db=%s"%history_db,logfile="fill_jobsub_history")
    dir = os.path.dirname(history_db)
    return dir

def loadArchive(afile,cleanup=False):
    fp = afile
    try:
        logger.log('catching up old file %s'% fp ,logfile="fill_jobsub_history")
        f = os.path.basename(fp)
        os.symlink(fp, os.path.join(os.path.realpath(os.curdir),f))
        createHistoryDump(f)
        createSqlFile(f)
        loadDatabase(f,cleanup)
    except:
        logger.log("%s"%sys.exc_info()[1],severity=logging.ERROR, logfile="fill_jobsub_history")
        logger.log("%s"%sys.exc_info()[1],severity=logging.ERROR, logfile="error")


def loadNewestArchive(cleanup=False):
    dir = os.path.dirname(condorHistoryFile())
    fp = ""
    t = 0
    for f in os.listdir(dir):
        if 'history.20' in f:
            try:
                logger.log('looking at %s'%f,logfile="fill_jobsub_history")
                fpx = os.path.join(dir,f)
                tx = os.path.getmtime(fpx)
                if tx > t:
                    logger.log('%s wins'%fpx,logfile="fill_jobsub_history")
                    t = tx
                    fp = fpx
            except:
                logger.log("%s"%sys.exc_info()[1], severity=logging.ERROR, logfile="fill_jobsub_history")
                logger.log("%s"%sys.exc_info()[1], severity=logging.ERROR, logfile="error")
    if fp:
        loadArchive(fp,cleanup)

def condorHistoryFile():
    cmd = "condor_config_val HISTORY"
    histfile , cmd_err = subprocessSupport.iexe_cmd(cmd)
    if cmd_err:
        logger.log("%s"%sys.exc_info()[1],severity=logging.ERROR, logfile="fill_jobsub_history")
        logger.log("%s"%sys.exc_info()[1],severity=logging.ERROR, logfile="error")
    return histfile

def keepUp():
    dir = historyDBDir()
    history_db = "%s/jobsub_history.db" % dir
    logger.log("changing to %s"%dir, logfile="fill_jobsub_history")
    os.chdir(dir)
    checkHistoryDB()
    try:
        os.makedirs('work')
    except:
        pass
    try:
        shutil.copy('jobsub_history.db', 'work')
        os.chdir('work')
        if os.path.exists('partial_history.sql'):
            shutil.copy('partial_history.sql', 'partial_history.sql.old')
        histfile = condorHistoryFile()
        cmd = "rsync %s . --size-only --backup --times" % histfile
        logger.log(cmd, logfile="fill_jobsub_history")
        cmd_out , cmd_err = subprocessSupport.iexe_cmd(cmd)
        logger.log(cmd_out, logfile="fill_jobsub_history")
        if cmd_err:
            logger.log(cmd_err, severity=logging.ERROR, logfile="fill_jobsub_history")
            logger.log(cmd_err, severity=logging.ERROR, logfile="error")
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
                fname = 'history'
        else:
            fname='history'
            loadNewestArchive()
        createHistoryDump(fname)
        createSqlFile(fname)
        loadDatabase(fname)
        shutil.copy('jobsub_history.db', history_db)

    except:
        logger.log(sys.exc_info()[1],severity=logging.ERROR, logfile="fill_jobsub_history")
        logger.log(sys.exc_info()[1],severity=logging.ERROR, logfile="error")

def pruneDB( ndays, dbname=None):

    if dbname:
        dir = os.path.dirname(dbname)
        history_db = dbname
        os.chdir(dir)
    else:
        dir = historyDBDir()
        history_db = "%s/jobsub_history.db"%dir
        logger.log("history_db is '%s'"% history_db, logfile="fill_jobsub_history")
        os.chdir(dir)
        shutil.copy('jobsub_history.db','work')
        os.chdir('work')

    logger.log('in dir %s db= %s'%(dir, history_db),logfile="fill_jobsub_history")

    sql1="""DELETE from jobsub_history WHERE 
                 qdate < datetime('now', '-%s days') AND 
                 jobstatus = 'X';""" % ndays

    sql2="""DELETE from jobsub_history WHERE 
                   completiondate < datetime('now', '-%s days') AND 
                   jobstatus = 'C';""" % ndays

    sql3="vacuum;"

    executeSQLCmds([sql1, sql2, sql3])

    if not dbname:
        shutil.copy('jobsub_history.db', history_db)

def executeSQLCmds(sql_list):
    conn = sqlite3.connect('jobsub_history.db')
    c = conn.cursor()
    for sql in sql_list:

        try:
            logger.log(sql,logfile="fill_jobsub_history")
            c.execute(sql)
            conn.commit()
        except sqlite3.Error as e:
            msg = "%s:%s " %(sql, str(e))
            logger.log(msg , severity=logging.ERROR, logfile="fill_jobsub_history")
            logger.log(msg , severity=logging.ERROR, logfile="error")
    conn.close()

def loadDatabase(filebase,cleanup=False):
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
                msg = "%s:%s " %(line, str(e))
                if 'is not unique' not in msg:
                    logger.log(msg, severity=logging.ERROR, logfile="fill_jobsub_history")
                    logger.log(msg, severity=logging.ERROR, logfile="error")
                    num_bad += 1
   
    totals = "%s lines in upload  %s successfully loaded  %s failed " % (num_total, num_good, num_bad)
    logger.log(totals, logfile="fill_jobsub_history")
    conn.close()
    if cleanup:
        try:
            if filebase != 'history' and os.path.exists(filebase):
                logger.log('cleaning up %s'%filebase, logfile="fill_jobsub_history")
                os.remove(filebase)
            f = '%s.dat'%filebase
            if os.path.exists(f):
                logger.log('cleaning up %s'%f, logfile="fill_jobsub_history")
                os.remove(f)
            f = '%s.sql'%filebase
            if os.path.exists(f):
                logger.log('cleaning up %s'%f, logfile="fill_jobsub_history")
                os.remove(f)
        except:
            logger.log("%s"%sys.exc_info()[1],severity=logging.ERROR, logfile="fill_jobsub_history")
            logger.log("%s"%sys.exc_info()[1],severity=logging.ERROR, logfile="error")



def run_prog():
    usage = '%prog [ Options]'

    parser = optparse.OptionParser(usage = usage, 
                                   description = \
                                   'parse htcondor history logs into jobsub_history database')

    parser.add_option('-v', 
                      dest='verbose',
                      action='store_true',
                      help='verbose mode')

    parser.add_option('--keepUp',
                      dest='keepUp',
                      action='store_true',
                      help=\
                      'incrementally parse and load history file from last run')

    parser.add_option('--pruneDB',
                      dest='pruneDB',
                      metavar='<number of days>',
                      default=None,
                      type='string',
                      help='remove history records older than '+\
                           '<number of days> from jobsub_history.db')

    parser.add_option('--pruneDBName',
                      dest='pruneDBName',
                      metavar='<db name>',
                      default=None,
                      type='string',
                      help='prune records from <db name>'+\
                           'the default is to prune the master db configured for server on this host')

    parser.add_option('--loadDBFromSQL',
                      dest='loadDBFromSQL',
                      metavar='<history_file>',
                      default=None,
                      type='string',
                      help='load history db from <history_file>.sql ')

    parser.add_option('--createHistoryDump',
                      dest='createHistoryDump',
                      metavar='<history_file>',
                      default=None,
                      type='string',
                      help='parse htcondor history log into intermediate <history_file>.dat ')

    parser.add_option('--createSqlFile', 
                      dest='createSqlFile', 
                      metavar='<history_file>',
                      default=None, 
                      type='string' , 
                      help='load history db from <history_file>.sql')

    parser.add_option('--loadArchive', 
                      dest='loadArchive', 
                      metavar='<archived_history_file>',
                      default=None, 
                      type='string' , 
                      help='load history db from <archived_history_file> (typically named history.YYYYMMDDhhmmss (a date)')

    parser.add_option('--createDB',
                      dest='createDB', 
                      metavar='<db_dir>',
                      default=None, 
                      type='string' , 
                      help='create jobsub_history.db <db_dir> if it does not already exist')

    parser.add_option('--loadNewestArchive',
                      dest='loadNewestArchive', 
                      action = 'store_true', 
                      help='populate jobsub_history.db with newest htcondor history archive ')

    parser.add_option('--cleanup',
                      dest='cleanup', 
                      action = 'store_true', 
                      help='clean up the intermediate sql and dat files')

    options, remainder = parser.parse_args(sys.argv)

    if options.verbose:
        print "options: %s" % options
        print "remainder %s" % remainder

    if options.loadDBFromSQL:
       loadDatabase(options.loadDBFromSQL, options.cleanup)
    elif options.createHistoryDump:
        createHistoryDump(options.createHistoryDump)
    elif options.createSqlFile:
        createSqlFile(options.createSqlFile)
    elif options.createDB:
        createDB(options.createDB)
    elif options.loadArchive:
        loadArchive(options.loadArchive,options.cleanup)
    elif options.loadNewestArchive:
        loadNewestArchive(options.cleanup)
    elif options.pruneDB:
        pruneDB(options.pruneDB, options.pruneDBName)
    elif options.keepUp:
        keepUp()
    else:
        parser.print_help()

if __name__ == '__main__':
    try:
        run_prog()
    except:

        logger.log("%s"%sys.exc_info()[1],
                   severity=logging.ERROR,
                   traceback=True,
                   logfile="fill_jobsub_history")

        logger.log("%s"%sys.exc_info()[1],
                   severity=logging.ERROR,
                   traceback=True,
                   logfile="error")
