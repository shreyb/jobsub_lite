#!/usr/bin/env python
# $Id$
import os
import sys
from JobSettings import JobSettings
from optparse import OptionGroup

class CdfSettings(JobSettings):
    def __init__(self):
        super(CdfSettings,self).__init__()
        self.settings['iama']='cdf'


    def initCmdParser(self):
        #cmdParser = self.cmdParser
        #print "CdfSettings.initCmdParser()"
        self.cdf_group = OptionGroup(self.cmdParser, "Cdf Specific Options")
        self.cmdParser.add_option_group(self.cdf_group)
        self.cdf_group.add_option("--outLocation", dest="outLocation",
                                 action="store",type="string",
                                 help="full path for output file (e.g. me@ncdfxx.fnal.gov:/home/me/out.tgz)")
        self.cdf_group.add_option("--procType", dest="procType",
                                 action="store",type="string",
                                 help="desired process type (e.g. short)")

        self.cdf_group.add_option("--start", dest="start",
                                 action="store",type="string",
                                 help="beginning segment number (e.g. 1)")
              
        self.cdf_group.add_option("--end", dest="end",
                                 action="store",type="string",
                                 help="ending segment number (e.g. 100))")

        self.cdf_group.add_option("--sections", dest="sections",
                                 action="store",type="string",
                                 help="segment range (e.g. 1-100)) start-end, use instead of --start --end")

        self.cdf_group.add_option("--dhaccess", dest="dhaccess",
                                 action="store",type="string",
                                 help="method for dataset access, options are SAM,userSAM,dcache,diskpool,MCGen,rootd,fcp/rcp, None")
                
##         self.cdf_group.add_option("-y", dest="enstorefiles",
##                                  action="append",
##                                  help="enstore files ")
            
##         self.cdf_group.add_option("-O", dest="msopt",
##                                  action="store",type="string",
##                                  help="optimize flag")
        return super(CdfSettings,self).initCmdParser()

    def makeWrapFilePreamble(self):
        super(CdfSettings,self).makeWrapFilePreamble()
        settings=self.settings
        f = open(settings['wrapfile'], 'a')
        f.write("###### BEGIN CDFSettings.makeWrapFilePreamble\n")
        f.write("###### END CDFSettings.makeWrapFilePreamble\n")
        f.close()

    def makeWrapFilePostamble(self):
        settings=self.settings
        f = open(settings['wrapfile'], 'a')
        f.write("###### BEGIN CDFSettings.makeWrapFilePostamble\n")
        f.write("###### END CDFSettings.makeWrapFilePostmble\n")
        f.close()
        super(CdfSettings,self).makeWrapFilePostamble()

    def makeWrapFile(self):
        super(CdfSettings,self).makeWrapFile()
        settings=self.settings
        f = open(settings['wrapfile'], 'a')
        f.write("###### BEGIN CDFSettings.makeWrapFile\n")
        f.write("###### END CDFSettings.makeWrapFile\n")
        f.close()



    def checkSanity(self):
        return super(CdfSettings,self).checkSanity()
        
