#!/usr/bin/env python
# $Id$
import os
from JobSettings import JobSettings
from optparse import *

class LbneSettings(JobSettings):
    def __init__(self):
        super(LbneSettings,self).__init__()
        self.settings['lbne_condor'] = os.environ.get("GROUP_CONDOR","/this/is/bogus")

        self.settings['defaultrelarea']="/grid/fermiapp/lbne/software_releases"



    def checkSanity(self):
        return super(LbneSettings,self).checkSanity()
        
    def initCmdParser(self):
        #print "LbneSettings initCmdParser"
        cmdParser = self.cmdParser
        self.lbne_group = OptionGroup(self.cmdParser, "Lbne Specific Options")
        self.cmdParser.add_option_group(self.lbne_group)

        
        self.lbne_group.add_option("-i", dest="reldir",
                action="store",type="string",
                help="release_directory for Lbne Software ")

        self.lbne_group.add_option("-t", dest="testreldir",
                action="store",type="string",
                help="release_directory for test Lbne Software ")
              
        self.lbne_group.add_option("-r", dest="rel",
                action="store",type="string",
                help="release_version for  Lbne Software ")
                
        self.lbne_group.add_option("-y", dest="enstorefiles",
                action="append",
                help="enstore files ")
            
        self.lbne_group.add_option("-O", dest="msopt",
                action="store",type="string",
                help="optimize flag")
        return super(LbneSettings,self).initCmdParser()
