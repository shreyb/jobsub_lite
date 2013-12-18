#!/usr/bin/env python
# $Id$
from JobSettings import JobSettings
import os
import string
from optparse import OptionGroup

class NovaSettings(JobSettings):
    def __init__(self):
        super(NovaSettings,self).__init__()
        self.settings['nova_condor'] = os.environ.get("GROUP_CONDOR","/this/is/bogus")

        self.settings['defaultrelarea']="/grid/fermiapp/nova/software_releases"
        self.settings['rp']=""
        self.settings['use_smu']=False


    


    def initParser(self):
        #parser = self.parser
        self.nova_group = OptionGroup(self.parser, "Nova Specific Options")
        self.parser.add_option_group(self.nova_group)
        self.nova_group.add_option("--SMU", dest="use_smu",
                                 action="store_true",default=False,
                                 help="steer jobs to HPC.SMU grid site")
        self.nova_group.add_option("-i", dest="reldir",
                                 action="store",type="string",
                                 help="release_directory for Nova Software ")

        self.nova_group.add_option("-t", dest="testreldir",
                                 action="store",type="string",
                                 help="release_directory for test Nova Software ")
              
        self.nova_group.add_option("-r", dest="rel",
                                 action="store",type="string",
                                 help="release_version for  Nova Software ")
                
##         self.nova_group.add_option("-y", dest="enstorefiles",
##                                  action="append",
##                                  help="enstore files ")
            
##         self.nova_group.add_option("-O", dest="msopt",
##                                  action="store",type="string",
##                                  help="optimize flag")
        return super(NovaSettings,self).initParser()

    def makeCommandFile(self,job_iter=0):
        #print "nova.makeCommandFile"
        settings=self.settings
        if settings['use_smu']:
            settings['use_gftp']=True
            self.makeSMUCommandFile()
        else:
            return super(NovaSettings,self).makeCommandFile(job_iter)
        
    def makeWrapFilePostamble(self):
        #print "nova.makeWrapFilePostamble"
        settings=self.settings
        if settings['use_smu']:
        
            self.makeSMUWrapFilePostamble()
        else:
            return super(NovaSettings,self).makeWrapFilePostamble()

    def makeSMUWrapFilePostamble(self):
        #print "makeSMUWrapFilePostamble"
        settings=self.settings
        script_args=''

        f = open(settings['wrapfile'], 'a')
        for x in settings['script_args']:
            script_args = script_args+x+" "
        basename = os.path.basename(settings['exe_script'])
        f.write("gftp   gsiftp://if-gridftp-nova.fnal.gov/%s file://${_CONDOR_SCRATCH_DIR}/%s  \n" % (settings['exe_script'],basename ))
        f.write("cd ${_CONDOR_SCRATCH_DIR} \n")

        if settings['joblogfile'] != "":
            f.write("./%s %s > %s\n" % (basename,script_args,settings['joblogfile']))
        else:
            f.write("./%s %s  \n" % \
                (basename,script_args))
 

        f.write("JOB_RET_STATUS=$?\n")


        for tag in settings['output_tag_array'].keys():
            f.write("if [ \"$(ls -A ${CONDOR_DIR_%s})\" ]; then\n" %(tag))
            f.write("\tchmod a+rwx ${CONDOR_DIR_%s}/*\n" % tag)
            f.write("\tmkdir -p %s\n" % settings['output_tag_array'][tag])
            if settings['use_gftp']:
                grp=string.replace(settings['group'],'mars','')
                f.write("lock\n")
                f.write("gftp  file://${CONDOR_DIR_%s}/ gsiftp://if-gridftp-%s.fnal.gov/%s/\n" % (tag,grp,settings['output_tag_array'][tag] ))
                f.write("lockfree\n")

            else:
                f.write("\t${CPN} ${CONDOR_DIR_%s}/* %s\n" % (tag,settings['output_tag_array'][tag] ))
            #f.write("\tchmod -R g+rw %s\n" % settings['output_tag_array'][tag])
            f.write("fi\n")
    
	#f.write(settings['exe_script']+" "+settings['script_args'])
        f.write("exit $JOB_RET_STATUS\n")
        f.close



    def makeSMUCommandFile(self):
        #print "makeSMUCommandFile"
        settings = self.settings
        f = open(settings['cmdfile'], 'w')
        f.write("universe      = vanilla\n")

        f.write("executable    = %s\n"%settings['exe_script'])
        args = ""
        if settings['tar_file_name']!="":
            args = "./"+os.path.basename(settings['exe_script'])+ " "
        for arg in settings['script_args']:
            args = args+" "+arg+" "
        for arg in settings['added_environment']:
            settings['environment'] = settings['environment']+";"+arg+'="'+os.environ.get(arg)+'"'
        f.write("arguments     = %s\n"%args)
        f.write("output        = %s\n"%settings['outfile'])
        f.write("error         = %s\n"%settings['errfile'])
        f.write("log           = %s\n"%settings['logfile'])
        f.write("environment   = %s\n"%settings['environment'])
        f.write("rank          = Mips / 2 + Memory\n")
        f.write("job_lease_duration = 3600\n")

        if settings['notify']==0:
            f.write("notification  = Never\n")
        elif settings['notify']==1:
            f.write("notification  = Error\n")
        else:
            f.write("notification  = Always\n")

    

        f.write("x509userproxy = %s\n" % settings['x509userproxy'])
        f.write("+RunOnGrid              = True\n")
        f.write("when_to_transfer_output = ON_EXIT\n")
        f.write("transfer_output         = True\n")
        f.write("transfer_error          = True\n")
        f.write("transfer_executable     = True\n")

            
        f.write("+DESIRED_Sites = \"SMU_nova\"\n")
        settings['requirements']=settings['requirements'] + \
                                  ' && (GLIDEIN_Site=="SMU_nova") && (TARGET.AGroup=="group_nova.smu")'

             
        f.write("+AccountingGroup = \"group_%s.%s\"\n"%(settings['accountinggroup'],settings['user']))
        f.write("+Agroup = \"group_nova.smu\"\n")

        f.write("requirements  = %s\n"%settings['requirements'])

        if len(settings['lines']) >0:            
	    for thingy in settings['lines']:
            	f.write("%s\n" % thingy)

	f.write("+GeneratedBy =\"%s\"\n"%settings['generated_by'])

        #f.write("%s"%settings['lines'])
        f.write("\n")
        f.write("\n")
        f.write("queue %s"%settings['queuecount'])

        f.close

 
    def checkSanity(self):
        return super(NovaSettings,self).checkSanity()
        
        
    def makeWrapFilePreamble(self):
        relfmt= """
  export NOVA_SETUP_DIR=/grid/fermiapp/nova/novaart/novasoft/setup/
  unset SETUP_UPS SETUPS_DIR
  . /grid/fermiapp/nova/products/db/.upsfiles/configure/v4_7_4a_Linux+2_/setups.sh

  setup_nova()
         {
           . $NOVA_SETUP_DIR/setup_novasoft_nusoft.sh $*
         }
  setup_nova -r  %s %s """


        relfmt2="""
    echo Running \'srt_setup -a\' in %s %s` 
    echo "here=\`/bin/pwd\`" 
    echo "cd "`${RP} $TESTRELDIR` 
    echo "srt_setup -a" 
    echo "cd $here" """
    
        relfmt3="""source /grid/fermiapp/nova/novaart/novasoft/srt/srt.sh
export EXTERNALS=/nusoft/app/externals
source $SRT_DIST/setup/setup_novasoft.sh -r %s"""

    
        #print "novasettings makeFilePreamble"
        super(NovaSettings,self).makeWrapFilePreamble()
        settings=self.settings
        #print settings['wrapfile']

        f = open(settings['wrapfile'], 'a')


        f.write("#NovaSettingsPreamble\n")

        if (settings.has_key('rel')):
            f.write(relfmt3 % (settings['rel']))
        if (settings.has_key('testreldir')):
            f.write("#NovaSettingsPreamble2\n")
            
            f.write(relfmt2 % (settings['rp'], settings['testreldir']))
            
        f.write("\n")
        f.close()
