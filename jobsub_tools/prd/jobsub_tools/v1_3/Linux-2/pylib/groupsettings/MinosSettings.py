#!/usr/bin/env python
# $Id$
from JobSettings import JobSettings
import os,commands
from optparse import OptionGroup

class MinosSettings(JobSettings):
    def __init__(self):
        super(MinosSettings,self).__init__()
        self.settings['minerva_condor'] = os.environ.get("MINERVA_CONDOR")

        self.settings['defaultrelarea']="/grid/fermiapp/minerva/software_releases"
        self.settings['rp']=" /afs/fnal.gov/files/code/e875/general/condor/scripts/realpath/realpath.pl"


    def initCmdParser(self):
        #print "MinosSettings initCmdParser"
        cmdParser = self.cmdParser
        self.minos_group = OptionGroup(self.cmdParser, "Minos Specific Options")
        self.cmdParser.add_option_group(self.minos_group)

        
        self.minos_group.add_option("-i", dest="reldir",
            action="store",type="string",
            help="release_directory for Minos Software ")

        self.minos_group.add_option("-t", dest="testreldir",
                action="store",type="string",
                help="release_directory for test Minos Software ")
              
        self.minos_group.add_option("-r", dest="rel",
                action="store",type="string",
                help="release_version for  Minos Software ")
                
        self.minos_group.add_option("-y", dest="enstorefiles",
                action="append",
                help="enstore files ")
            
        self.minos_group.add_option("-O", dest="msopt",
                action="store",type="string",
                help="optimize flag")
        return super(MinosSettings,self).initCmdParser()

    def makeWrapFilePreamble(self):
        relfmt= """
  export MINOS_SETUP_DIR=/grid/fermiapp/minos/minossoft/setup
  #unset SETUP_UPS SETUPS_DIR
  #. /grid/fermiapp/nova/products/db/.upsfiles/configure/v4_7_4a_Linux+2_/setups.sh

  setup_minos()
         {
           . $MINOS_SETUP_DIR/setup_minossoft_FNALU.sh $*
         }
  setup_minos -r  %s %s """


        relfmt2="""
    echo Running 'srt_setup -a' in `%s %s` 
    here=`/bin/pwd` 
    cd ` %s %s`
    srt_setup -a 
    cd $here 


"""
  
        #print "minossettings makeFilePreamble"
        super(MinosSettings,self).makeWrapFilePreamble()
        settings=self.settings
        #print settings['wrapfile']

        f = open(settings['wrapfile'], 'a')


        #f.write("#MinosSettingsPreamble\n")
	f.write("export MINOS_ENSTORE=/grid/fermiapp/minos/enstore\n")
	f.write("source /grid/fermiapp/minos/enstore/setup_aliases.sh\n")
	f.write("""export PATH="/grid/fermiapp/minos/enstore:${PATH}"\n""")
	f.write("export MINOS_GRIDDB=/grid/fermiapp/minos/griddb\n")
	f.write("""export PATH="/grid/fermiapp/minos/griddb:${PATH}"\n""")

        if (settings.has_key('rel')):
	    f.write("export ENV_TSQL_URL=`/grid/fermiapp/minos/griddb/choose_db_server`")
	    f.write("echo Setting database URL to $ENV_TSQL_URL")
            f.write(relfmt % (settings['rel'], settings['msopt']))
	    
        if (settings.has_key('testreldir')):
            f.write("#MinosSettingsPreamble2")
            
            f.write(relfmt2 % (settings['rp'], settings['testreldir'],settings['rp'],settings['testreldir']))
            
        f.write("\n")
        f.close()

    def checkSanity(self):
        return super(MinosSettings,self).checkSanity()
        
