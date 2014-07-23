#!/usr/bin/env python
# $Id$
import os
from JobSettings import JobSettings
from optparse import *

class CdfSettings(JobSettings):
    def __init__(self):
        super(CdfSettings,self).__init__()

    def makeWrapFilePreamble(self):
        super(CdfSettings,self).makeWrapFilePreamble()
        
        settings=self.settings

        f = open(settings['wrapfile'], 'a')


        f.write("#CDFSettingsPreamble\n")

        f.close()

    def checkSanity(self):
        return super(CdfSettings,self).checkSanity()
        
    def initCmdParser(self):
        return super(CdfSettings,self).initCmdParser()
