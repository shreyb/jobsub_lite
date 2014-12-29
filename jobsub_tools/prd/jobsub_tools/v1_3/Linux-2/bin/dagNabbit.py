#!/usr/bin/env python

import os
import string
import sys
import stat
import readline
import commands
import pprint
import re
import datetime
import time
import subprocess
from JobsubConfigParser import JobsubConfigParser

docString = """
 $Id$
"""
manual = """
INTRODUCTION
============
%s is a script which generates and optionally runs a condor 
DAG (directed acyclic graph) of condor jobs.  For illustration, suppose
that you have 5 jobs A,B,C,D,E, that you want to run using condor. 
Job B requires A to run first, C and D require the output form B, 
and E requires the input from C and D.
A graphic representation would be:

                                  A
                                  |
                                  B
                                 / \\
                                C   D
                                 \ /
                                  E

Further suppose for illustration that job A is submitted to condor 
using the command jobsub -g jobA.sh, job B by jobsub -g jobB.sh, etc.
The jobsub script has a '-n' option, which generates but does not submit
the condor command file. When this option is added, the condor command file
is sent to stdout.  My output for the command 'jobsub -g -n jobA.sh' was:

 /minerva/app/users/condor-tmp/dbox/jobA.sh_20110830_105651_1.cmd

THIS SCRIPT REQUIRES THAT ONE OR MORE CONDOR COMMAND FILES OF THE FORM
/path/to/my/command/file/runMyJob.cmd  are sent to stdout, this
is captured and put in the condor DAG command file

INPUT FILE BASICS
=================
The input file for the DAG generator in this example would look like this:
<serial>
jobsub -g -n jobA.sh
jobsub -g -n jobB.sh
</serial>
<parallel>
jobsub -g -n jobC.sh
jobsub -g -n jobD.sh
</parallel>
<serial>
jobsub -g -n jobE.sh
</serial>

INPUT FILE MACROS
============
It is common for scripts to have inputs to 'sweep' through a set of parameters.
Let us suppose that the jobA.sh et al accept input paramters like so:

./jobA.sh -firstRun (some_number) -lastRun (some_bigger_number) -title (something arbitrary but meaningful to user)

The 'macros' section of the input file handles this requirement like so:

<macros>
$first = 1
$last = 100
$formatted_date=`%s`
$current_directory  = `pwd`
$whatever = 'some string that has significance elsewhere'
</macros>
<serial>
jobsub -g -n $current_directory/jobA.sh -firstRun $first -lastRun $last -title $whatever
jobsub -g -n $current_directory/jobB.sh -firstRun $first -lastRun $last -title $whatever
</serial>
<parallel>
jobsub -g -n jobC.sh -firstRun $first -lastRun $last -title $whatever
jobsub -g -n jobD.sh -firstRun $first -lastRun $last -title $whatever
</parallel>
<serial>
jobsub -g -n jobE.sh -firstRun $first -lastRun $last -title $whatever
</serial>

IT IS IMPORTANT that EACH COMMAND GENERATE THE SAME NUMBER OF CONDOR CMD
FILES, or the resultant dag will be incorrect.

BEGINJOB AND FINISHJOB SCRIPTS
=============================

Users have the option of running a pre-staging script prior to thier dag
and a cleanup script afterwards using the <beginjob> and <finishjob> tags.
The scripts specified this way run on the submission machine and not on the 
condor worker nodes as the serial and parallel jobs do.

An example script using these tags follows:

<macros>
$project_name = 'project_3'
$dataset_def = 'dataset_5'
$first = 1
$last = 100
$whatever  = Joes Third Attempt At Running This
</macros>
<beginjob>
startSAMProject.sh $dataset_def $project_name
</beginjob>
<serial>
jobsub -g -n jobA.sh -project_name $project_name
</serial><parallel>
jobsub -g -n jobC.sh -firstRun $first -lastRun $last -title $whatever
jobsub -g -n jobD.sh -firstRun $first -lastRun $last -title $whatever
</parallel>
<serial>
jobsub -g -n jobE.sh -firstRun $first -lastRun $last -title $whatever
</serial>
<finishjob>
clean_up_SAM_project.sh $project_name
</finishjob>


RUNNING A DAG
==============
%s -input_file (inputFile) -s will submit your generated DAG to condor.  The -m (pos_integer) 
flag will ensure that only (pos_integer) number of your jobs will run at the same time, which
is intended to prevent overwhelming shared resources such as databases.
"""
usage = """
usage: %s -i input_file [-o output_dag] [-h(elp)] [-s(ubmit)] [-submit_host some_machine.fnal.gov ][--maxConcurrent  max_concurrent_jobs ]

for detailed instructions on how to use:
%s -manual | less
"""
cmd_file_dummy = """
universe      = vanilla
executable    = %s/returnOK_%s.sh
output        = %s/returnOK_%s.out
error         = %s/returnOK_%s.err
log           = %s/returnOK_%s.log
environment   = PROCESS=$(Process);CONDOR_TMP=%s;CONDOR_EXEC=%s
rank          = Mips / 2 + Memory
notification  = Error
requirements  = ((Arch=="X86_64") || (Arch=="INTEL"))
+RUN_ON_HEADNODE = TRUE

queue
"""
wrap_file_dummy = """#!/bin/sh
#
exit 0
"""
class DagParser(object):
        
        def __init__(self):
                
                self.jobList = []
                self.jobNameList=[]
                self.macroList=[]
                self.beginJobList=[]
                self.finishJobList=[]
                
                self.jobDict = {}
                self.jobNameDict = {}
                self.macroDict = {}
                self.beginJobDict = {}
                self.finishJobDict = {}
                
                self.processingMacros = False
                self.processingSerial = False
                self.processingParallel = False
                self.processingBeginJob = False
                self.processingFinishJob = False
                self.redundancy = 0
                self.condor_tmp = os.environ.get("CONDOR_TMP")
                


#######################################################################

        def startSerial(self,s):
                
                s=s.lower()
                if s.find("<serial>")>=0:
                        self.processingSerial = True
                        return True
                return False

        
        def endSerial(self,s):
                
                s=s.lower()
                if s.find("</serial>")>=0:
                        self.processingSerial = False
                        return True
                return False
        
#######################################################################


        def startParallel(self,s):
                
                s=s.lower()
                if s.find("<parallel>")>=0:
                        self.processingParallel = True
                        return True
                return False




        def endParallel(self,s):
                
                s=s.lower()
                if s.find("</parallel>")>=0:
                        self.processingParallel = False
                        return True
                return False

#######################################################################

        def startBeginJob(self,s):
                
                s=s.lower()
                if s.find("<beginjob>")>=0:
                        self.processingBeginJob = True
                        return True
                return False

        
        def endBeginJob(self,s):
                
                s=s.lower()
                if s.find("</beginjob>")>=0:
                        self.processingBeginJob = False
                        return True
                return False

                        
        def isInBeginJob(self,s):

                if self.startBeginJob(s):
                        self.processingBeginJob = True
                return self.processingBeginJob


        
        def processBeginJob(self,line):
                
                if self.endBeginJob(line):
                        self.processingBeginJob = False
                else:
                        
                        line=line.strip()
                        self.beginJobList.append(line)
                        #print "self.beginJobList=",self.beginJobList

#######################################################################
        
        def startFinishJob(self,s):
                
                s=s.lower()
                if s.find("<finishjob>")>=0:
                        self.processingFinishJob = True
                        return True
                return False

        
        def endFinishJob(self,s):
                
                s=s.lower()
                if s.find("</finishjob>")>=0:
                        self.processingFinishJob = False
                        return True
                return False

        def isInFinishJob(self,s):

                if self.startFinishJob(s):
                        self.processingFinishJob = True
                return self.processingFinishJob

        
        def processFinishJob(self,line):
                
                if self.endFinishJob(line):
                        self.processingFinishJob = False
                        self.finishJobList.append("mailer.py ")
                else:
                        line=line.strip()
                        self.finishJobList.append(line)
#######################################################################


        
        def startMacros(self,s):
                
                s=s.lower()
                if s.find("<macros>")>=0:
                        self.processingMacros = True
                        return True
                return False

        
        def endMacros(self,s):
                
                s=s.lower()
                if s.find("</macros>")>=0:
                        self.processingMacros = False
                        return True
                return False
        
        
        def isInMacros(self,s):

                if self.startMacros(s):
                        self.processingMacros = True
                return self.processingMacros

        
        def processMacro(self,line):
                #print "processMacro input=",line
                if self.endMacros(line):
                        self.processingMacros = False
                elif line.find("=")>=0:
                        [a,b]=line.split("=")
                        a=a.strip()
                        b=b.strip()
                        self.macroList.append(a)
                        self.macroDict[a]=b
                        if(b.find("`")==0):
                                if(b.find("`",1)==(len(b)-1)):
                                        cmd=b[1:len(b)-1]
                                        (retVal,val)=commands.getstatusoutput(cmd)
                                        #print "command %s returns %s"%(b,val)
                                        self.macroDict[a]=val
#######################################################################


        def reportState(self):
                print "processingSerial:%s processingParallel:%s"%\
                        (self.processingSerial,self.processingParallel)
                print self.jobList
                print self.jobDict

        def digestInputFile(self, infile=""):
                #strip out comments starting with '#'
                if infile=="":
                        infile=sys.argv[1]
                r =re.compile("#.*")
                plist = []
                if len(sys.argv)>1:
                        f = open(infile,"r")
                        i=0
                        j=0
                        for line in f:
                                line=line.strip()
                                line=r.sub('',line)
                                #print "input line " , line
                                if self.startSerial(line):
                                        pass
                                elif self.endSerial(line):
                                        pass
                                elif self.startParallel(line):
                                        plist = []
                                        pass
                                elif self.endParallel(line):
                                        self.jobList.append(plist)
                                        pass
                                elif self.isInMacros(line):
                                        self.processMacro(line)
                                        pass
                                elif self.isInBeginJob(line):
                                        self.processBeginJob(line)
                                        pass
                                elif self.isInFinishJob(line):
                                        self.processFinishJob(line)
                                        pass
                                
                                elif len(line)>0:
                                        for mac in self.macroList:
                                                line = line.replace(mac,self.macroDict[mac])
                                        #line = line.replace('$CONDOR_TMP',self.condor_tmp)
                                        val=""
                                        (retVal,val)=commands.getstatusoutput(line)
                                        ##proc = subprocess.Popen(line,shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                                        ##retVal = proc.wait()
                                        ##for op in proc.stdout:
                                        ##        val=val+op
                                        if retVal:
                                                print "error processing command %s"%line
                                                print val
                                        else:
                                                j=j+1
                                                condor_cmd=''
                                                condor_cmd_list =[]
                                                biglist = val.split()
                                                ncmds=0
                                                i=0
                                                for word in biglist:
                                                        if word.find(".cmd")>=0 and word not in condor_cmd_list:
                                                                ncmds=ncmds+1
                                                                condor_cmd = word        
                                                                jobName="Jb_%d_%d"%(j,i)
                                                                self.jobNameList.append(jobName)
                                                                self.jobDict[condor_cmd]=jobName
                                                                self.jobNameDict[jobName]=condor_cmd
                                                                condor_cmd_list.append(condor_cmd)
                                                                i=i+1
                                                if self.processingSerial:
                                                        self.jobList.append(tuple(condor_cmd_list))
                                                if self.processingParallel:
                                                        plist.append(tuple(condor_cmd_list))
                                                if (self.redundancy != 0 and self.redundancy != len(condor_cmd_list)):
                                                        print "ERROR: different number of '.cmd' files detected"
                                                        print "between jobs in input file! This will generate"
                                                        print "an incorrect DAG!  aborting......"
                                                        #sys.exit(-1)
                                                        self.redundancy = len(condor_cmd_list)
                                                else:
                                                        self.redundancy = len(condor_cmd_list)
                                                
                                                #reportState()
                        cntr=0
                        for line in self.beginJobList:
                                for mac in self.macroList:
                                        line = line.replace(mac,self.macroDict[mac])
                                        #print line
                                        self.beginJobList[cntr]=line
                                cntr=cntr+1
                        cntr=0
                        for line in self.finishJobList:
                                for mac in self.macroList:
                                        line = line.replace(mac,self.macroDict[mac])
                                        #print line
                                        self.finishJobList[cntr]=line
                                cntr=cntr+1


        def getJobName(self,jlist,i,j=0):

                if isinstance(jlist[i],tuple):
                        retval=self.jobDict[jlist[i][j]]
                        return retval

                elif isinstance(jlist[i],list):
                        retval=""
                        for l in jlist[i]:
                                retval=retval+" "+ self.getJobName(l,0,j)
                        return retval
                else:

                        retval=self.jobDict[jlist[j]]
                        return retval



        def generateDependencies(self,outputFile,jlist):
                f=open(outputFile,"a")
                jend=len(jlist)
                i=0
                
                if len(self.beginJobList)>0:
                        j=0
                        while(j<self.redundancy):
                                l = "parent JOB_BEGIN child %s\n"% self.getJobName(jlist,i,j)
                                f.write(l)
                                j=j+1

                

                while (i<jend-1):
                        j=0
                        while(j<self.redundancy):
                                l = "parent %s child %s\n"%\
                                    (self.getJobName(jlist,i,j),self.getJobName(jlist,i+1,j))
                                f.write(l)
                                j=j+1
                        i=i+1

                if len(self.finishJobList)>0:
                        j=0
                        
                        while(j<self.redundancy):
                                l = "parent %s child JOB_FINISH\n"% self.getJobName(jlist,i,j)
                                f.write(l)
                                j=j+1

                        
                f.close()
                
        def writeDummyCmdFile(self):
                
                condor_tmp=os.environ.get("CONDOR_TMP")
                if condor_tmp is None:
                        print "ERROR, CONDOR_TMP env variable needs to be set!"
                        sys.exit(-1)
                        
                condor_exec=os.environ.get("CONDOR_EXEC")
                if condor_exec is None:
                        print "ERROR, CONDOR_EXEC env variable needs to be set!"
                        sys.exit(-1)
                
                now = datetime.datetime.now()
                filebase = "%s%02d%02d_%02d%02d%02d"%(now.year,now.month,now.day,now.hour,now.minute,now.second)
                cmd_file_name = "%s/dummy%s.cmd" %(condor_tmp,filebase)
                wrap_file_name = "%s/returnOK_%s.sh" %(condor_exec,filebase)
                cmd_file = cmd_file_dummy % (condor_exec,filebase,condor_tmp,filebase,condor_tmp,\
                                              filebase,condor_tmp,filebase,condor_tmp,condor_exec)

                f=open(cmd_file_name,"w")
                f.write(cmd_file)
                f.close()
                f=open(wrap_file_name,"w")
                f.write(wrap_file_dummy)
                f.close()
                os.chmod(wrap_file_name,stat.S_IRWXU| stat.S_IRGRP|stat.S_IXGRP |stat.S_IROTH|stat.S_IXOTH)
                return cmd_file_name
        

        def generateDag(self,outputFile=None):

                f=open(outputFile,"w")
                l = "DOT %s.dot UPDATE\n" % outputFile
                f.write(l)

                if len(self.beginJobList)>0:
                        
                        l = "JOB JOB_BEGIN %s\n" % self.writeDummyCmdFile() 
                        f.write(l)
                        
                for n in self.jobNameList:
                        l = "JOB " + n + " "+ self.jobNameDict[n]+"\n"
                        f.write(l)

                if len(self.finishJobList)>0:
                        time.sleep(1)
                        l = "JOB JOB_FINISH %s \n" % self.writeDummyCmdFile()
                        f.write(l)

                if len(self.beginJobList)>0:
                        l = "SCRIPT PRE JOB_BEGIN %s \n" % self.beginJobList[1]
                        f.write(l)
                if len(self.finishJobList)>0:
                        l = "SCRIPT POST JOB_FINISH %s \n" % self.finishJobList[1]
                        f.write(l)

                f.close()
                self.generateDependencies(outputFile,self.jobList)

class ArgParser(object):
        def __init__(self,cfp):
                cfp.findConfigFile()
                self.inputFile = ""
                self.outputFile = ""
                self.runDag = False
                self.viewDag = False
                self.maxJobs = 0
                self.submitHost = os.environ.get("SUBMIT_HOST")
                self.condorSetup = cfp.get(self.submitHost,"condor_setup_cmd")
                self.group = os.environ.get("GROUP")
                allowed = cfp.supportedGroups()
                if len(self.condorSetup)>0 and self.condorSetup.find(';')<0:
                    self.condorSetup=self.condorSetup+";"

                if self.group not in allowed:
                        print "ERROR do not run this script as member of group %s" % self.group
                        print "export GROUP=one of %s and try again"% allowed
                        sys.exit(-1)
                        

                i=0

                for arg in sys.argv:
                        i=i+1
                        
                        if arg in ["--h", "-h", "--help", "-help"]:
                                self.printHelp()
                        if arg in [ "-man", "-manual"]:
                                self.printManual()
                        if arg in ["--inputFile", "-input_file","-i" ]:
                                self.inputFile = sys.argv[i]
                        if arg in ["--outputFile", "-output_file", "-o" ]:
                                self.outputFile = sys.argv[i]
                        if arg in ["--maxConcurrent", "--maxRunning", "-max_running", "-m" ]:
                                self.maxJobs = int(sys.argv[i])
                        if arg in ["--submit", "-submit", "-s" ]:
                                self.runDag = True
                        if arg in ["--submitHost", "-submit_host" ]:
                                self.submitHost = sys.argv[i]
                if i==1:
                        self.printHelp()
                        sys.exit(0)
                                
                if self.outputFile=="":
                        cmd = """date +%Y%m%d_%H%M%S"""
                        #commands=JobUtils()
                        (retVal,val)=commands.getstatusoutput(cmd)
                        now = val.rstrip()
                        condor_tmp=os.environ.get("CONDOR_TMP")                        
                        home=os.environ.get("HOME")
                        if condor_tmp=="" or condor_tmp == None :
                                self.outputFile = home+"/submit.%s.dag"%now
                        else:
                                self.outputFile = condor_tmp+"/submit.%s.dag"%now
                        print "generated DAG saved as ", self.outputFile
        def report(self):
                print "====================================="
                print "inputFile = ",self.inputFile
                print "outputFile = ",self.outputFile
                print "runDag =",self.runDag
                print "maxJobs =",self.maxJobs
                
        def printHelp(self):
                h = os.path.basename(sys.argv[0])
                helpFile = usage % (h,h)
                print helpFile
                sys.exit(0)

        def printManual(self):
                m = os.path.basename(sys.argv[0])
                df = """date +%Y%m%d_%H%M%S_%N"""
                manFile = manual % (m,df,m)
                print manFile
                sys.exit(0)

class JobRunner(object):
        def __init__(self): 
                pass
        def doSubmit(self,args=None):

                cmd=""

                #commands=JobUtils()
                (retVal,host)=commands.getstatusoutput("uname -n")
                ups_shell = os.environ.get("UPS_SHELL")
                if ups_shell is None:
                        ups_shell="sh"
                if ups_shell == "csh" and args.condorSetup.find( '/opt/condor/condor.sh')>=0 :
                    args.condorSetup = 'source /opt/condor/condor.csh ;'

                if host == args.submitHost:
                        cmd = """ %s  condor_submit_dag -dont_suppress_notification  """ % args.condorSetup
                else:
                        cmd = """ssh %s " %s  condor_submit_dag -dont_suppress_notification """ % (args.submitHost,args.condorSetup)
                cmd2 = "/grid/fermiapp/common/graphviz/zgrviewer/zgrview "
                if args.maxJobs > 0:
                        cmd = cmd + " -maxjobs %d " % args.maxJobs
                usr=os.environ.get("USER")
                grp=os.environ.get("GROUP")

                cmd = cmd + """ -append "+Owner=\\"%s\\"" -append "+AccountingGroup=\\"group_%s.%s\\"" """%(usr,grp,usr)
                cmd = cmd + args.outputFile
                if host != args.submitHost:
                        cmd = cmd + ' "'
                print "executing ", cmd
                (retVal,val)=commands.getstatusoutput(cmd)
                if retVal:
                        print "ERROR executing ",cmd
                        print val
                        retVal=retVal%256
                        if retVal==0:
                            retVal=1
                        sys.exit(retVal)
                print val


        

if __name__ == '__main__':
        c=JobsubConfigParser()
        args=ArgParser(c)
        d=DagParser()
        d.digestInputFile(args.inputFile)
        d.generateDag(args.outputFile)
        if args.runDag:
                j = JobRunner()
                j.doSubmit(args)

